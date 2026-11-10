"""PNG RGB/RGBA LSB watermark framing and Ed25519 verification."""

import base64
from dataclasses import dataclass
import hashlib
import hmac
from io import BytesIO
import json
import re
import struct
import warnings
import uuid

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from PIL import Image, UnidentifiedImageError


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
FRAME_MAGIC = b"IPGW"
FRAME_VERSION = 1
FRAME_FLAGS = 0
STEGO_DOMAIN = b"IPGUARD-PNG-LSB-WATERMARK-V1\x00"
MAX_IMAGE_BYTES = 50 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
MAX_IMAGE_DIMENSION = 10_000
MAX_PAYLOAD_BYTES = 4 * 1024 * 1024
KEY_ID_BYTES = 16
SIGNATURE_BYTES = 64
PREFIX_HEADER_BYTES = 106
FIXED_HEADER_BYTES = PREFIX_HEADER_BYTES + SIGNATURE_BYTES
_KEY_ID_RE = re.compile(r"^[0-9a-f]{32}$")


class PngSteganographyError(ValueError):
    """Safe, stable error code for invalid PNG or watermark input."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class PngInfo:
    width: int
    height: int
    mode: str
    channels: int


@dataclass(frozen=True)
class WatermarkFrame:
    watermark_id: uuid.UUID
    source_asset_id: uuid.UUID
    derivative_asset_id: uuid.UUID
    payload: bytes
    payload_sha256: bytes
    signing_key_id: str
    version: int
    signed_prefix: bytes
    signature: bytes


@dataclass(frozen=True)
class WatermarkVerification:
    verified: bool
    status: str
    watermark_id: uuid.UUID | None = None
    source_asset_id: uuid.UUID | None = None
    derivative_asset_id: uuid.UUID | None = None
    format_version: int | None = None
    payload: bytes | None = None


def _check_png_ihdr(data: bytes, *, max_image_bytes: int, max_pixels: int, max_dimension: int) -> PngInfo:
    if not isinstance(data, bytes) or len(data) < 33:
        raise PngSteganographyError("INVALID_PNG", "PNG input is incomplete.")
    if len(data) > max_image_bytes:
        raise PngSteganographyError("IMAGE_TOO_LARGE", "PNG exceeds the encoded size limit.")
    if data[:8] != PNG_SIGNATURE:
        raise PngSteganographyError("INVALID_PNG", "Input is not a PNG image.")

    ihdr_length = struct.unpack(">I", data[8:12])[0]
    if ihdr_length != 13 or data[12:16] != b"IHDR":
        raise PngSteganographyError("INVALID_PNG", "PNG IHDR is invalid.")

    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", data[16:29]
    )
    if width < 1 or height < 1:
        raise PngSteganographyError("INVALID_DIMENSIONS", "PNG dimensions must be positive.")
    if width > max_dimension or height > max_dimension or width * height > max_pixels:
        raise PngSteganographyError("IMAGE_DIMENSIONS_EXCEEDED", "PNG dimensions exceed the processing limit.")
    if bit_depth != 8 or color_type not in (2, 6):
        raise PngSteganographyError("UNSUPPORTED_PNG_MODE", "Only 8-bit truecolor RGB and RGBA PNGs are supported.")
    if compression != 0 or filtering != 0 or interlace not in (0, 1):
        raise PngSteganographyError("INVALID_PNG", "PNG IHDR parameters are invalid.")

    return PngInfo(width, height, "RGBA" if color_type == 6 else "RGB", 4 if color_type == 6 else 3)


def _decode_png(data: bytes, *, max_image_bytes: int, max_pixels: int, max_dimension: int) -> tuple[Image.Image, PngInfo]:
    info = _check_png_ihdr(
        data,
        max_image_bytes=max_image_bytes,
        max_pixels=max_pixels,
        max_dimension=max_dimension,
    )
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as probe:
                if probe.format != "PNG" or probe.size != (info.width, info.height) or probe.mode != info.mode:
                    raise PngSteganographyError("INVALID_PNG", "PNG decoder metadata does not match IHDR.")
                probe.verify()
            with Image.open(BytesIO(data)) as image:
                if image.format != "PNG" or image.mode != info.mode or image.size != (info.width, info.height):
                    raise PngSteganographyError("INVALID_PNG", "PNG decoder metadata does not match IHDR.")
                image.load()
                return image.copy(), info
    except PngSteganographyError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise PngSteganographyError("IMAGE_DIMENSIONS_EXCEEDED", "PNG exceeds the decoder resource limit.") from exc
    except (OSError, ValueError, UnidentifiedImageError) as exc:
        raise PngSteganographyError("INVALID_PNG", "PNG decoding or integrity validation failed.") from exc


def _rgb_component_offset(bit_index: int, channels: int) -> int:
    pixel_index, color_channel = divmod(bit_index, 3)
    return pixel_index * channels + color_channel


def _write_lsb_bytes(pixel_bytes: bytearray, frame: bytes, channels: int) -> None:
    bit_index = 0
    for value in frame:
        for shift in range(7, -1, -1):
            offset = _rgb_component_offset(bit_index, channels)
            pixel_bytes[offset] = (pixel_bytes[offset] & 0xFE) | ((value >> shift) & 1)
            bit_index += 1


def _read_lsb_bytes(pixel_bytes: bytes, byte_count: int, channels: int) -> bytes:
    output = bytearray(byte_count)
    for bit_index in range(byte_count * 8):
        offset = _rgb_component_offset(bit_index, channels)
        output[bit_index // 8] |= (pixel_bytes[offset] & 1) << (7 - bit_index % 8)
    return bytes(output)


def _key_id(public_key_bytes: bytes) -> str:
    return hashlib.sha256(public_key_bytes).digest()[:KEY_ID_BYTES].hex()


def load_public_keys(public_keys_json: str | None) -> dict[str, Ed25519PublicKey]:
    """Parse and validate every configured raw Ed25519 public key and its ID."""
    if not public_keys_json:
        return {}
    try:
        raw_map = json.loads(public_keys_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise PngSteganographyError("SIGNING_KEY_CONFIGURATION_INVALID", "Public key configuration is invalid.") from exc
    if not isinstance(raw_map, dict):
        raise PngSteganographyError("SIGNING_KEY_CONFIGURATION_INVALID", "Public key configuration must be a JSON object.")

    result: dict[str, Ed25519PublicKey] = {}
    for configured_id, encoded_key in raw_map.items():
        if not isinstance(configured_id, str) or not _KEY_ID_RE.fullmatch(configured_id):
            raise PngSteganographyError("SIGNING_KEY_CONFIGURATION_INVALID", "A public key ID is invalid.")
        if not isinstance(encoded_key, str):
            raise PngSteganographyError("SIGNING_KEY_CONFIGURATION_INVALID", "A public key value is invalid.")
        try:
            key_bytes = base64.b64decode(encoded_key, validate=True)
            if len(key_bytes) != 32 or _key_id(key_bytes) != configured_id:
                raise ValueError("key id mismatch")
            result[configured_id] = Ed25519PublicKey.from_public_bytes(key_bytes)
        except (ValueError, TypeError) as exc:
            raise PngSteganographyError("SIGNING_KEY_CONFIGURATION_INVALID", "A public key does not match its key ID.") from exc
    return result


def load_signing_key(settings) -> tuple[Ed25519PrivateKey, str, dict[str, Ed25519PublicKey]]:
    """Load a raw 32-byte Ed25519 seed and require its public pair in the key map."""
    public_keys = load_public_keys(settings.stego_public_keys_json)
    active_id = settings.stego_active_key_id
    encoded_private = settings.stego_signing_private_key_b64
    if not active_id or not _KEY_ID_RE.fullmatch(active_id) or not encoded_private:
        raise PngSteganographyError("SIGNING_KEY_UNAVAILABLE", "Steganography signing key is unavailable.")
    try:
        seed = base64.b64decode(encoded_private, validate=True)
        if len(seed) != 32:
            raise ValueError("invalid seed length")
        private_key = Ed25519PrivateKey.from_private_bytes(seed)
        derived_public = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        if _key_id(derived_public) != active_id:
            raise ValueError("active key ID mismatch")
        configured_public = public_keys.get(active_id)
        if configured_public is None:
            raise ValueError("active public key missing")
        configured_public_bytes = configured_public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        if not hmac.compare_digest(derived_public, configured_public_bytes):
            raise ValueError("private/public key mismatch")
        return private_key, active_id, public_keys
    except (ValueError, TypeError) as exc:
        raise PngSteganographyError("SIGNING_KEY_CONFIGURATION_INVALID", "Steganography signing key configuration is invalid.") from exc


def _frame_prefix(
    *,
    watermark_id: uuid.UUID,
    source_asset_id: uuid.UUID,
    derivative_asset_id: uuid.UUID,
    payload: bytes,
    signing_key_id: str,
) -> bytes:
    return b"".join(
        (
            FRAME_MAGIC,
            bytes((FRAME_VERSION, FRAME_FLAGS)),
            watermark_id.bytes,
            source_asset_id.bytes,
            derivative_asset_id.bytes,
            struct.pack(">I", len(payload)),
            hashlib.sha256(payload).digest(),
            bytes.fromhex(signing_key_id),
        )
    )


def embed_png(
    png_bytes: bytes,
    payload: bytes,
    *,
    source_asset_id: uuid.UUID,
    derivative_asset_id: uuid.UUID,
    watermark_id: uuid.UUID,
    settings,
) -> bytes:
    """Embed a signed frame in row-major RGB LSBs, preserving RGBA alpha bytes."""
    if not isinstance(payload, bytes):
        raise PngSteganographyError("INVALID_PAYLOAD", "Payload must be bytes.")
    max_payload = min(settings.stego_max_payload_bytes, MAX_PAYLOAD_BYTES)
    if len(payload) > max_payload:
        raise PngSteganographyError("PAYLOAD_TOO_LARGE", "Payload exceeds the configured limit.")
    if derivative_asset_id == source_asset_id:
        raise PngSteganographyError("INVALID_ASSET_ID", "Source and derivative IDs must differ.")

    image, info = _decode_png(
        png_bytes,
        max_image_bytes=min(settings.stego_max_image_bytes, MAX_IMAGE_BYTES),
        max_pixels=min(settings.stego_max_image_pixels, MAX_IMAGE_PIXELS),
        max_dimension=min(settings.stego_max_image_dimension, MAX_IMAGE_DIMENSION),
    )
    private_key, active_id, _ = load_signing_key(settings)
    prefix = _frame_prefix(
        watermark_id=watermark_id,
        source_asset_id=source_asset_id,
        derivative_asset_id=derivative_asset_id,
        payload=payload,
        signing_key_id=active_id,
    )
    signature = private_key.sign(STEGO_DOMAIN + prefix + payload)
    frame = prefix + signature + payload
    capacity = (info.width * info.height * 3) // 8
    if len(frame) > capacity:
        raise PngSteganographyError("PAYLOAD_EXCEEDS_CAPACITY", "Payload and frame exceed PNG LSB capacity.")

    pixel_bytes = bytearray(image.tobytes())
    _write_lsb_bytes(pixel_bytes, frame, info.channels)
    output = Image.frombytes(info.mode, image.size, bytes(pixel_bytes))
    encoded = BytesIO()
    output.save(encoded, format="PNG", optimize=False)
    result = encoded.getvalue()
    if len(result) > min(settings.stego_max_image_bytes, MAX_IMAGE_BYTES):
        raise PngSteganographyError("OUTPUT_IMAGE_TOO_LARGE", "Encoded derivative exceeds the image size limit.")
    return result


def parse_png_frame(png_bytes: bytes, *, settings) -> WatermarkFrame:
    """Extract a structurally valid frame; does not release it as trusted payload."""
    image, info = _decode_png(
        png_bytes,
        max_image_bytes=min(settings.stego_max_image_bytes, MAX_IMAGE_BYTES),
        max_pixels=min(settings.stego_max_image_pixels, MAX_IMAGE_PIXELS),
        max_dimension=min(settings.stego_max_image_dimension, MAX_IMAGE_DIMENSION),
    )
    pixel_bytes = image.tobytes()
    capacity = (info.width * info.height * 3) // 8
    if capacity < FIXED_HEADER_BYTES:
        raise PngSteganographyError("TRUNCATED_FRAME", "PNG does not have enough capacity for a complete frame header.")
    fixed = _read_lsb_bytes(pixel_bytes, FIXED_HEADER_BYTES, info.channels)
    if fixed[:4] != FRAME_MAGIC:
        raise PngSteganographyError("WATERMARK_NOT_FOUND", "No supported watermark frame was found.")
    version, flags = fixed[4], fixed[5]
    if version != FRAME_VERSION:
        raise PngSteganographyError("UNSUPPORTED_VERSION", "Watermark frame version is not supported.")
    if flags != FRAME_FLAGS:
        raise PngSteganographyError("UNSUPPORTED_FLAGS", "Watermark frame flags are not supported.")

    watermark_id = uuid.UUID(bytes=fixed[6:22])
    source_asset_id = uuid.UUID(bytes=fixed[22:38])
    derivative_asset_id = uuid.UUID(bytes=fixed[38:54])
    payload_length = struct.unpack(">I", fixed[54:58])[0]
    payload_digest = fixed[58:90]
    signing_key_id = fixed[90:106].hex()
    max_payload = min(settings.stego_max_payload_bytes, MAX_PAYLOAD_BYTES)
    frame_length = FIXED_HEADER_BYTES + payload_length
    if payload_length > max_payload:
        raise PngSteganographyError("PAYLOAD_TOO_LARGE", "Watermark payload exceeds the configured limit.")
    if frame_length > capacity:
        raise PngSteganographyError("FRAME_EXCEEDS_CAPACITY", "Watermark frame length exceeds PNG capacity.")

    complete_frame = _read_lsb_bytes(pixel_bytes, frame_length, info.channels)
    prefix = complete_frame[:PREFIX_HEADER_BYTES]
    signature = complete_frame[PREFIX_HEADER_BYTES:FIXED_HEADER_BYTES]
    payload = complete_frame[FIXED_HEADER_BYTES:]
    if not hmac.compare_digest(hashlib.sha256(payload).digest(), payload_digest):
        raise PngSteganographyError("CHECKSUM_MISMATCH", "Watermark payload checksum does not match.")
    return WatermarkFrame(
        watermark_id=watermark_id,
        source_asset_id=source_asset_id,
        derivative_asset_id=derivative_asset_id,
        payload=payload,
        payload_sha256=payload_digest,
        signing_key_id=signing_key_id,
        version=version,
        signed_prefix=prefix,
        signature=signature,
    )


def verify_png_watermark(
    png_bytes: bytes,
    *,
    expected_source_asset_id: uuid.UUID | None,
    expected_derivative_asset_id: uuid.UUID,
    expected_watermark_id: uuid.UUID | None,
    settings,
) -> WatermarkVerification:
    """Verify framing, database lineage, payload checksum, and Ed25519 signature."""
    frame: WatermarkFrame | None = None
    try:
        frame = parse_png_frame(png_bytes, settings=settings)
        if frame.derivative_asset_id != expected_derivative_asset_id:
            raise PngSteganographyError("DERIVATIVE_ID_MISMATCH", "Frame derivative ID does not match this asset.")
        if frame.source_asset_id != expected_source_asset_id:
            raise PngSteganographyError("SOURCE_ID_MISMATCH", "Frame source ID does not match asset lineage.")
        if frame.watermark_id != expected_watermark_id:
            raise PngSteganographyError("WATERMARK_ID_MISMATCH", "Frame watermark ID does not match asset metadata.")

        public_keys = load_public_keys(settings.stego_public_keys_json)
        public_key = public_keys.get(frame.signing_key_id)
        if public_key is None:
            raise PngSteganographyError("UNKNOWN_SIGNING_KEY", "Watermark signing key is not configured.")
        try:
            public_key.verify(frame.signature, STEGO_DOMAIN + frame.signed_prefix + frame.payload)
        except InvalidSignature as exc:
            raise PngSteganographyError("INVALID_SIGNATURE", "Watermark signature is invalid.") from exc

        return WatermarkVerification(
            True,
            "VERIFIED",
            frame.watermark_id,
            frame.source_asset_id,
            frame.derivative_asset_id,
            frame.version,
            frame.payload,
        )
    except PngSteganographyError as exc:
        return WatermarkVerification(
            False,
            exc.code,
            frame.watermark_id if frame else None,
            frame.source_asset_id if frame else None,
            frame.derivative_asset_id if frame else None,
            frame.version if frame else None,
            None,
        )
