"""PNG LSB framing, resource bounds, signing, and verification tests."""

import base64
from io import BytesIO
import json
import struct
from types import SimpleNamespace
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from alembic.migration import MigrationContext
from alembic.operations import Operations
from PIL import Image
import pytest
from sqlalchemy import create_engine, text

from app.services.png_steganography import (
    FIXED_HEADER_BYTES,
    FRAME_MAGIC,
    FRAME_VERSION,
    PngSteganographyError,
    _check_png_ihdr,
    _key_id,
    _rgb_component_offset,
    embed_png,
    load_public_keys,
    load_signing_key,
    parse_png_frame,
    verify_png_watermark,
)


def _keys(seed: bytes | None = None):
    seed = seed or bytes(range(32))
    private = Ed25519PrivateKey.from_private_bytes(seed)
    public_bytes = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    key_id = _key_id(public_bytes)
    settings = SimpleNamespace(
        stego_signing_private_key_b64=base64.b64encode(seed).decode("ascii"),
        stego_active_key_id=key_id,
        stego_public_keys_json=json.dumps({key_id: base64.b64encode(public_bytes).decode("ascii")}),
        stego_max_image_bytes=50 * 1024 * 1024,
        stego_max_image_pixels=20_000_000,
        stego_max_image_dimension=10_000,
        stego_max_payload_bytes=4 * 1024 * 1024,
    )
    return private, public_bytes, key_id, settings


def _png(mode="RGB", size=(64, 64)):
    image = Image.new(mode, size)
    if mode == "RGB":
        image.putdata([((i * 3) % 256, (i * 7) % 256, (i * 11) % 256) for i in range(size[0] * size[1])])
    else:
        image.putdata([((i * 3) % 256, (i * 7) % 256, (i * 11) % 256, (i * 13) % 256) for i in range(size[0] * size[1])])
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def _embed(data=None, payload=b"watermark payload", **kwargs):
    _, _, _, settings = _keys()
    source_id = kwargs.pop("source_asset_id", uuid.uuid4())
    derivative_id = kwargs.pop("derivative_asset_id", uuid.uuid4())
    watermark_id = kwargs.pop("watermark_id", uuid.uuid4())
    result = embed_png(
        data or _png(),
        payload,
        source_asset_id=source_id,
        derivative_asset_id=derivative_id,
        watermark_id=watermark_id,
        settings=kwargs.pop("settings", settings),
    )
    return result, source_id, derivative_id, watermark_id


def _rewrite_lsb_byte(png_bytes: bytes, bit_offset: int, value: int) -> bytes:
    image = Image.open(BytesIO(png_bytes))
    channels = 4 if image.mode == "RGBA" else 3
    pixels = bytearray(image.tobytes())
    for bit in range(8):
        component = _rgb_component_offset(bit_offset + bit, channels)
        pixels[component] = (pixels[component] & 0xFE) | ((value >> (7 - bit)) & 1)
    rewritten = Image.frombytes(image.mode, image.size, bytes(pixels))
    stream = BytesIO()
    rewritten.save(stream, format="PNG")
    return stream.getvalue()


@pytest.mark.parametrize("mode", ["RGB", "RGBA"])
def test_embed_extract_verify_round_trip_and_preserve_rgba_alpha(mode):
    original = _png(mode)
    output, source_id, derivative_id, watermark_id = _embed(original)
    _, _, _, settings = _keys()
    image = Image.open(BytesIO(original))
    output_image = Image.open(BytesIO(output))

    assert output_image.mode == mode
    if mode == "RGBA":
        assert image.getchannel("A").tobytes() == output_image.getchannel("A").tobytes()

    frame = parse_png_frame(output, settings=settings)
    assert frame.payload == b"watermark payload"
    assert frame.watermark_id == watermark_id
    assert frame.source_asset_id == source_id
    assert frame.derivative_asset_id == derivative_id
    verified = verify_png_watermark(
        output,
        expected_source_asset_id=source_id,
        expected_derivative_asset_id=derivative_id,
        expected_watermark_id=watermark_id,
        settings=settings,
    )
    assert verified.verified is True
    assert verified.payload == b"watermark payload"


def test_row_major_rgb_channel_order_and_msb_first_are_deterministic():
    output, *_ = _embed()
    image = Image.open(BytesIO(output))
    pixels = image.tobytes()
    observed = []
    for bit_index in range(32):
        observed.append(pixels[_rgb_component_offset(bit_index, 3)] & 1)
    observed_bytes = bytes(
        sum(observed[offset + bit] << (7 - bit) for bit in range(8))
        for offset in range(0, len(observed), 8)
    )
    assert observed_bytes == FRAME_MAGIC


@pytest.mark.parametrize("bit_depth,color_type", [(16, 2), (8, 0), (8, 3), (8, 4)])
def test_ihdr_rejects_unsupported_depth_or_color_type_before_decode(bit_depth, color_type):
    ihdr = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR"
    ihdr += struct.pack(">IIBBBBB", 64, 64, bit_depth, color_type, 0, 0, 0) + b"\x00\x00\x00\x00"
    with pytest.raises(PngSteganographyError, match="Only 8-bit"):
        _check_png_ihdr(ihdr, max_image_bytes=1000, max_pixels=10000, max_dimension=1000)


def test_dimensions_are_checked_before_pillow_decoding():
    fake = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR"
    fake += struct.pack(">IIBBBBB", 100_000, 100_000, 8, 2, 0, 0, 0) + b"\x00\x00\x00\x00"
    with pytest.raises(PngSteganographyError, match="dimensions exceed"):
        _check_png_ihdr(fake, max_image_bytes=1000, max_pixels=20_000_000, max_dimension=10_000)


def test_malformed_png_is_rejected():
    _, _, _, settings = _keys()
    with pytest.raises(PngSteganographyError, match="PNG"):
        embed_png(
            b"\x89PNG\r\n\x1a\nnot actually PNG",
            b"x",
            source_asset_id=uuid.uuid4(),
            derivative_asset_id=uuid.uuid4(),
            watermark_id=uuid.uuid4(),
            settings=settings,
        )


def test_capacity_and_payload_limits_are_enforced():
    _, _, _, settings = _keys()
    with pytest.raises(PngSteganographyError, match="capacity"):
        embed_png(
            _png(size=(16, 16)),
            b"x",
            source_asset_id=uuid.uuid4(),
            derivative_asset_id=uuid.uuid4(),
            watermark_id=uuid.uuid4(),
            settings=settings,
        )
    settings.stego_max_payload_bytes = 1
    with pytest.raises(PngSteganographyError, match="configured limit"):
        embed_png(
            _png(),
            b"too long",
            source_asset_id=uuid.uuid4(),
            derivative_asset_id=uuid.uuid4(),
            watermark_id=uuid.uuid4(),
            settings=settings,
        )


def test_signature_checksum_and_database_identity_fail_closed_without_payload():
    output, source_id, derivative_id, watermark_id = _embed()
    _, _, _, settings = _keys()
    frame = parse_png_frame(output, settings=settings)
    damaged_signature = _rewrite_lsb_byte(output, 106 * 8, frame.signature[0] ^ 1)
    result = verify_png_watermark(
        damaged_signature,
        expected_source_asset_id=source_id,
        expected_derivative_asset_id=derivative_id,
        expected_watermark_id=watermark_id,
        settings=settings,
    )
    assert result.verified is False
    assert result.status == "INVALID_SIGNATURE"
    assert result.payload is None

    result = verify_png_watermark(
        output,
        expected_source_asset_id=uuid.uuid4(),
        expected_derivative_asset_id=derivative_id,
        expected_watermark_id=watermark_id,
        settings=settings,
    )
    assert result.status == "SOURCE_ID_MISMATCH"
    assert result.payload is None

    result = verify_png_watermark(
        output,
        expected_source_asset_id=source_id,
        expected_derivative_asset_id=uuid.uuid4(),
        expected_watermark_id=watermark_id,
        settings=settings,
    )
    assert result.status == "DERIVATIVE_ID_MISMATCH"
    assert result.payload is None


def test_payload_checksum_and_declared_capacity_are_checked_before_release():
    output, *_ = _embed()
    _, _, _, settings = _keys()
    payload_corrupted = _rewrite_lsb_byte(output, FIXED_HEADER_BYTES * 8, 0x00)
    with pytest.raises(PngSteganographyError) as checksum_error:
        parse_png_frame(payload_corrupted, settings=settings)
    assert checksum_error.value.code == "CHECKSUM_MISMATCH"

    oversized_frame = output
    for offset, value in enumerate((0, 0, 0x13, 0x88)):
        oversized_frame = _rewrite_lsb_byte(oversized_frame, (54 + offset) * 8, value)
    with pytest.raises(PngSteganographyError) as capacity_error:
        parse_png_frame(oversized_frame, settings=settings)
    assert capacity_error.value.code == "FRAME_EXCEEDS_CAPACITY"


def test_unknown_magic_version_and_truncated_frame_have_stable_results():
    _, _, _, settings = _keys()
    plain = _png(size=(24, 24))
    with pytest.raises(PngSteganographyError) as no_frame:
        parse_png_frame(plain, settings=settings)
    assert no_frame.value.code in {"WATERMARK_NOT_FOUND", "TRUNCATED_FRAME"}

    output, *_ = _embed()
    unsupported = _rewrite_lsb_byte(output, 32, FRAME_VERSION + 1)
    with pytest.raises(PngSteganographyError, match="version"):
        parse_png_frame(unsupported, settings=settings)

    with pytest.raises(PngSteganographyError, match="header"):
        parse_png_frame(_png(size=(10, 10)), settings=settings)


def test_every_public_key_id_is_validated_and_signing_fails_closed():
    _, public_bytes, key_id, settings = _keys()
    bad_map = {key_id: base64.b64encode(public_bytes).decode("ascii"), "0" * 32: base64.b64encode(public_bytes).decode("ascii")}
    with pytest.raises(PngSteganographyError, match="does not match"):
        load_public_keys(json.dumps(bad_map))

    settings.stego_signing_private_key_b64 = None
    with pytest.raises(PngSteganographyError, match="unavailable"):
        load_signing_key(settings)


def test_old_public_key_verifies_after_signing_key_rotation():
    _, old_public, old_id, settings = _keys(bytes(range(32)))
    source_id, derivative_id, watermark_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    old_png = embed_png(
        _png(), b"signed by old key", source_asset_id=source_id,
        derivative_asset_id=derivative_id, watermark_id=watermark_id, settings=settings,
    )
    new_private = Ed25519PrivateKey.from_private_bytes(bytes(reversed(range(32))))
    new_public = new_private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    new_id = _key_id(new_public)
    settings.stego_signing_private_key_b64 = base64.b64encode(bytes(reversed(range(32)))).decode("ascii")
    settings.stego_active_key_id = new_id
    settings.stego_public_keys_json = json.dumps({
        old_id: base64.b64encode(old_public).decode("ascii"),
        new_id: base64.b64encode(new_public).decode("ascii"),
    })
    result = verify_png_watermark(
        old_png,
        expected_source_asset_id=source_id,
        expected_derivative_asset_id=derivative_id,
        expected_watermark_id=watermark_id,
        settings=settings,
    )
    assert result.verified is True
    assert result.payload == b"signed by old key"


def test_migration_0009_is_incremental_and_leaves_legacy_asset_metadata_null(tmp_path):
    import importlib.util
    from pathlib import Path

    migration_path = (
        Path(__file__).parents[1]
        / "app"
        / "db"
        / "migrations"
        / "versions"
        / "0009_png_lsb_derivatives.py"
    )
    spec = importlib.util.spec_from_file_location("png_stego_migration", migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.down_revision == "0008_audit_hash_chain"

    engine = create_engine(f"sqlite:///{tmp_path / 'png-stego-migration.sqlite'}")
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE assets (id CHAR(32) PRIMARY KEY, original_filename VARCHAR(255))"))
            connection.execute(text("INSERT INTO assets (id, original_filename) VALUES ('legacy-id', 'old.png')"))
            context = MigrationContext.configure(connection)
            with Operations.context(context):
                migration.upgrade()
            row = connection.execute(
                text("SELECT source_asset_id, derivative_type, watermark_id, stego_format_version FROM assets WHERE id='legacy-id'")
            ).one()
            assert tuple(row) == (None, None, None, None)
            fk_rows = connection.execute(text("PRAGMA foreign_key_list(assets)")).all()
            assert any(row[2] == "assets" and row[6].upper() == "RESTRICT" for row in fk_rows)
    finally:
        engine.dispose()
