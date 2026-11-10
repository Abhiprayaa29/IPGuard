"""IPGuard Milestone 4 — Real Browser Acceptance Testing Script.

Executes complete end-to-end browser interactions via Playwright:
1. Injects hardware-authenticated session into browser context.
2. Navigates to Asset Vault and validates UI readiness.
3. Uploads an authentic 256x256 RGB master PNG image.
4. Opens watermark configuration modal and inputs custom metadata.
5. Embeds signed PNG LSB watermark and observes loading and success states.
6. Downloads the watermarked derivative PNG directly through the browser.
7. Conducts independent cryptographic and visual inspection of the downloaded file.
8. Verifies and extracts watermark through browser modals.
9. Validates tamper resistance and captures high-resolution screenshots.
"""

import base64
from datetime import datetime, timedelta, timezone
from io import BytesIO
import json
import math
import os
from pathlib import Path
import secrets
import sys
import uuid

from PIL import Image
from playwright.sync_api import sync_playwright
import psycopg

# Paths
WORKSPACE = Path("D:/Projects/IPGuard")
BACKEND_DIR = WORKSPACE / "backend"
SCREENSHOTS_DIR = WORKSPACE / "docs" / "screenshots" / "m4_acceptance"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Add backend to sys.path for direct crypto verification
sys.path.insert(0, str(BACKEND_DIR))
from app.services.png_steganography import parse_png_frame, verify_png_watermark
from app.core.config import get_settings


def create_test_master_png(filename: str, width: int = 256, height: int = 256) -> str:
    """Generate a rich RGB master PNG image with color gradients."""
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            r = int((x / width) * 255)
            g = int((y / height) * 255)
            b = int(((x + y) / (width + height)) * 255)
            pixels[x, y] = (r, g, b)
    filepath = str(SCREENSHOTS_DIR / filename)
    img.save(filepath, format="PNG")
    return filepath


def compute_psnr(img1_path: str, img2_path: str) -> tuple[float, float]:
    """Compute Mean Squared Error (MSE) and Peak Signal-to-Noise Ratio (PSNR)."""
    im1 = Image.open(img1_path).convert("RGB")
    im2 = Image.open(img2_path).convert("RGB")
    assert im1.size == im2.size, "Image dimensions must match for PSNR calculation"
    w, h = im1.size
    p1 = list(im1.getdata())
    p2 = list(im2.getdata())
    total_sq_diff = 0.0
    for (r1, g1, b1), (r2, g2, b2) in zip(p1, p2):
        total_sq_diff += (r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2
    mse = total_sq_diff / (w * h * 3)
    if mse == 0:
        return 0.0, float("inf")
    psnr = 20.0 * math.log10(255.0 / math.sqrt(mse))
    return mse, psnr


def setup_auth_session() -> tuple[str, str]:
    """Create an approved auth session in PostgreSQL for browser testing."""
    conn = psycopg.connect(
        "postgresql://ipguard:96e53c7bc2cee94c27d88acc99d85af6809765b79ccc1ec126571f6c0af24461@127.0.0.1:5432/ipguard",
        autocommit=True,
    )
    cur = conn.cursor()
    cur.execute("SELECT id, device_id FROM devices WHERE status = 'ACTIVE' LIMIT 1")
    row = cur.fetchone()
    if not row:
        raise RuntimeError("No active device found in PostgreSQL database.")
    device_db_id, device_id = row

    token = secrets.token_hex(32)
    session_id = uuid.uuid4()
    challenge = secrets.token_hex(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=3)

    cur.execute(
        """
        INSERT INTO auth_sessions (id, session_token, challenge_nonce, session_type, status, client_origin, device_id, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (session_id, token, challenge, "AUTHENTICATION", "APPROVED", "http://127.0.0.1:5173", device_db_id, expires_at),
    )
    conn.close()
    print(f"[AUTH] Registered hardware session token: {token} for device: {device_id}")
    return token, device_id


def run_browser_acceptance():
    print("[ACCEPTANCE] Starting Milestone 4 Browser Acceptance Test...")
    auth_token, device_id = setup_auth_session()

    console_logs = []
    page_errors = []
    failed_requests = []

    # Prepare Master PNG
    master_png_path = create_test_master_png("master_artwork_256.png")
    print(f"[IMAGE] Created master PNG at: {master_png_path}")

    test_metadata = {
        "copyright": "© 2026 IPGuard Vault Acceptance Test. All rights reserved.",
        "license": "Enterprise Proprietary License (M4 Verified)",
        "text": "Confidential - Authorized Production Review Build",
        "description": "Master derivative with hardware-bound Ed25519 digital watermark.",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1366, "height": 860},
            accept_downloads=True,
            permissions=["clipboard-read", "clipboard-write"],
        )
        page = context.new_page()

        # Log listeners
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: page_errors.append(str(err)))
        page.on("requestfailed", lambda req: failed_requests.append(f"{req.method} {req.url}: {req.failure}"))

        # Step 1: Open Base URL & Inject Session Token
        print("[STEP 1] Navigating to http://127.0.0.1:5173/ ...")
        page.goto("http://127.0.0.1:5173/")
        page.wait_for_load_state("networkidle")

        # Inject session token into sessionStorage
        page.evaluate(
            f"token => sessionStorage.setItem('ipguard_session_access_token', token)",
            auth_token,
        )

        # Step 2: Open Asset Vault
        print("[STEP 2] Navigating to http://127.0.0.1:5173/assets ...")
        page.goto("http://127.0.0.1:5173/assets")
        page.wait_for_selector("text=Asset Vault & Steganography", timeout=10_000)
        page.wait_for_selector("text=Hardware-Bound Active", timeout=10_000)
        page.screenshot(path=str(SCREENSHOTS_DIR / "01_asset_vault_initial.png"))
        print("[SCREENSHOT] 01_asset_vault_initial.png saved.")

        # Step 3: Upload Master PNG
        print("[STEP 3] Uploading master PNG image...")
        page.click('button:has-text("Upload Asset")')
        page.wait_for_selector("text=Upload Digital Asset", timeout=5_000)
        page.set_input_files('input[type="file"]', master_png_path)
        page.wait_for_selector("text=master_artwork_256.png", timeout=5_000)
        page.click('button[type="submit"]:has-text("Encrypt & Save")')

        # Wait for asset row to appear in table
        page.wait_for_selector('td:has-text("master_artwork_256.png")', timeout=15_000)
        page.wait_for_timeout(1000)
        page.screenshot(path=str(SCREENSHOTS_DIR / "02_asset_uploaded.png"))
        print("[SCREENSHOT] 02_asset_uploaded.png saved.")

        # Step 4: Open Watermark Configuration Modal
        print("[STEP 4] Opening Watermark Configuration Form...")
        row = page.locator('tr:has-text("master_artwork_256.png")').first
        watermark_btn = row.locator('button:has-text("Watermark")')
        watermark_btn.click()

        page.wait_for_selector("text=Embed Cryptographic Watermark", timeout=5_000)
        page.wait_for_selector("text=Ed25519 (Hardware)", timeout=5_000)
        page.screenshot(path=str(SCREENSHOTS_DIR / "03_watermark_config_modal.png"))
        print("[SCREENSHOT] 03_watermark_config_modal.png saved.")

        # Step 5: Fill Watermark Configuration Form
        print("[STEP 5] Configuring custom watermark metadata...")
        # Copyright Notice
        copyright_input = page.locator('input[placeholder*="Your Name"]')
        copyright_input.fill(test_metadata["copyright"])

        # License
        license_input = page.locator('input[placeholder*="CC-BY-NC"]')
        license_input.fill(test_metadata["license"])

        # Custom text
        custom_input = page.locator('input[placeholder*="Confidential Asset"]')
        custom_input.fill(test_metadata["text"])

        # Description
        desc_input = page.locator('textarea[placeholder*="distribution metadata"]')
        desc_input.fill(test_metadata["description"])

        page.wait_for_timeout(500)

        # Step 6: Submit Embedding
        print("[STEP 6] Embedding signed watermark...")
        page.click('button:has-text("Embed Watermark")')

        # Verify success banner
        page.wait_for_selector("text=Watermark Embedded Successfully!", timeout=15_000)
        page.wait_for_selector("text=master_artwork_256.watermarked.png", timeout=5_000)
        page.screenshot(path=str(SCREENSHOTS_DIR / "04_embed_success.png"))
        print("[SCREENSHOT] 04_embed_success.png saved.")

        # Step 7: Download Watermarked PNG from UI
        print("[STEP 7] Downloading watermarked PNG image through browser...")
        download_path = str(SCREENSHOTS_DIR / "master_artwork_256.watermarked.png")
        with page.expect_download() as download_info:
            page.click('button:has-text("Download Watermarked Image")')
        download = download_info.value
        download.save_as(download_path)
        print(f"[DOWNLOAD] Saved downloaded file to: {download_path}")

        # Step 8: Independent Binary & Cryptographic Validation of Downloaded File
        print("[STEP 8] Performing binary and cryptographic validation on downloaded file...")
        with open(download_path, "rb") as f:
            downloaded_bytes = f.read()

        # Check magic bytes: not ciphertext, true PNG
        assert downloaded_bytes[:8] == b"\x89PNG\r\n\x1a\n", "CRITICAL: Downloaded file is not a valid PNG binary!"
        print("[VALIDATION] Magic bytes verified: True PNG format (not ciphertext).")

        # Check Pillow readability and size
        downloaded_img = Image.open(BytesIO(downloaded_bytes))
        assert downloaded_img.format == "PNG", f"Expected PNG format, got {downloaded_img.format}"
        assert downloaded_img.size == (256, 256), f"Expected 256x256, got {downloaded_img.size}"
        assert downloaded_img.mode == "RGB", f"Expected RGB mode, got {downloaded_img.mode}"
        print(f"[VALIDATION] Image readable: {downloaded_img.format} {downloaded_img.size} {downloaded_img.mode}")

        # Compute PSNR vs original
        mse, psnr = compute_psnr(master_png_path, download_path)
        print(f"[VALIDATION] Visual Fidelity: MSE = {mse:.6f}, PSNR = {psnr:.2f} dB (Imperceptible Watermark)")
        assert psnr > 45.0, f"Watermark degraded visual fidelity (PSNR: {psnr:.2f} dB)"

        # Verify LSB frame and Ed25519 signature
        backend_settings = get_settings()
        frame = parse_png_frame(downloaded_bytes, settings=backend_settings)
        assert frame is not None, "Failed to parse IPGW frame from downloaded image"
        print(f"[VALIDATION] IPGW Frame parsed: Watermark UUID = {frame.watermark_id}, Version = {frame.version}")

        # Extract payload and verify JSON metadata
        extracted_json = json.loads(frame.payload.decode("utf-8"))
        assert extracted_json["copyright"] == test_metadata["copyright"]
        assert extracted_json["license"] == test_metadata["license"]
        assert extracted_json["text"] == test_metadata["text"]
        assert extracted_json["description"] == test_metadata["description"]
        print("[VALIDATION] Extracted payload matches original metadata 100%!")

        # Step 9: Close Modal and Verify Asset Vault Table Row
        print("[STEP 9] Inspecting Asset Vault table for derivative record...")
        page.goto("http://127.0.0.1:5173/assets")
        page.wait_for_selector('td:has-text("master_artwork_256.watermarked.png")', timeout=10_000)
        page.wait_for_selector("text=PNG_LSB Derivative", timeout=10_000)
        page.screenshot(path=str(SCREENSHOTS_DIR / "05_vault_with_derivative.png"))
        print("[SCREENSHOT] 05_vault_with_derivative.png saved.")

        # Step 10: Trigger Watermark Verification Modal
        print("[STEP 10] Testing Watermark Verification modal...")
        deriv_row = page.locator('tr:has-text("master_artwork_256.watermarked.png")').first
        verify_btn = deriv_row.locator('button[title*="Verify Watermark"]')
        verify_btn.click()

        page.wait_for_selector("text=Watermark Verified & Authentic", timeout=10_000)
        page.wait_for_selector("text=Ed25519 digital signature and SHA-256 payload integrity check passed", timeout=5_000)
        page.screenshot(path=str(SCREENSHOTS_DIR / "06_verify_success_modal.png"))
        print("[SCREENSHOT] 06_verify_success_modal.png saved.")

        # Step 11: Trigger Payload Extraction Modal from Verification Modal
        print("[STEP 11] Testing Watermark Payload Extraction modal...")
        page.click('button:has-text("Extract Verified Payload")')
        page.wait_for_selector("text=Verified Watermark Payload", timeout=10_000)
        page.wait_for_selector(f"text={test_metadata['copyright']}", timeout=5_000)
        page.wait_for_selector(f"text={test_metadata['license']}", timeout=5_000)
        page.screenshot(path=str(SCREENSHOTS_DIR / "07_extract_payload_modal.png"))
        print("[SCREENSHOT] 07_extract_payload_modal.png saved.")

        # Test Copy button
        page.click('button:has-text("Copy")')
        page.wait_for_selector("text=Copied", timeout=3_000)
        page.click('button:has-text("Close")')

        # Step 12: Inspect Modal Interaction
        print("[STEP 12] Testing Inspect Modal on derivative asset...")
        deriv_row = page.locator('tr:has-text("master_artwork_256.watermarked.png")').first
        inspect_btn = deriv_row.locator('button[title*="Inspect Metadata"]')
        inspect_btn.click()

        page.wait_for_selector("text=Steganography Lineage", timeout=5_000)
        page.wait_for_selector("text=Watermark UUID", timeout=5_000)
        page.wait_for_selector("text=XChaCha20-Poly1305", timeout=5_000)
        page.wait_for_timeout(1000)  # Wait for decrypted preview image
        page.screenshot(path=str(SCREENSHOTS_DIR / "08_derivative_inspect_modal.png"))
        print("[SCREENSHOT] 08_derivative_inspect_modal.png saved.")
        page.click('button:has-text("Close")')

        # Step 13: Filter Tabs Interaction
        print("[STEP 13] Testing Watermarked Filter Tab...")
        page.click('button:has-text("Watermarked (M4)")')
        page.wait_for_timeout(500)
        page.screenshot(path=str(SCREENSHOTS_DIR / "09_watermarked_filter_tab.png"))
        print("[SCREENSHOT] 09_watermarked_filter_tab.png saved.")

        # Reset to all
        page.click('button:has-text("all")')

        # Step 14: Tamper Detection Validation
        print("[STEP 14] Testing Tamper Detection on pixel-altered image...")
        tampered_img = Image.open(download_path).convert("RGB")
        pixel = tampered_img.getpixel((0, 0))
        tampered_img.putpixel((0, 0), (pixel[0] ^ 1, pixel[1], pixel[2]))
        tampered_path = str(SCREENSHOTS_DIR / "tampered_artwork.png")
        tampered_img.save(tampered_path, format="PNG")

        tamper_verification = verify_png_watermark(
            open(tampered_path, "rb").read(),
            expected_source_asset_id=frame.source_asset_id,
            expected_derivative_asset_id=frame.derivative_asset_id,
            expected_watermark_id=frame.watermark_id,
            settings=backend_settings,
        )
        assert tamper_verification.verified is False
        assert tamper_verification.status in ("WATERMARK_NOT_FOUND", "SIGNATURE_INVALID", "CHECKSUM_MISMATCH")
        print(f"[TAMPER] Tampered image rejected with status: {tamper_verification.status}")

        browser.close()

    # Save summary report JSON
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "browser": "Chromium 1366x860",
        "device_id": device_id,
        "master_image": {
            "path": master_png_path,
            "dimensions": "256x256",
            "format": "PNG",
            "mode": "RGB",
        },
        "downloaded_derivative": {
            "path": download_path,
            "dimensions": "256x256",
            "format": "PNG",
            "mode": "RGB",
            "psnr_db": round(psnr, 2),
            "mse": round(mse, 6),
            "magic_bytes_valid": True,
            "watermark_id": str(frame.watermark_id),
            "source_asset_id": str(frame.source_asset_id),
            "format_version": frame.version,
            "signature_valid": True,
            "sha256_digest_valid": True,
        },
        "extracted_metadata": extracted_json,
        "tamper_detection": {
            "tested": True,
            "pixel_modified": "(0, 0) red LSB",
            "verified": False,
            "rejection_status": tamper_verification.status,
        },
        "browser_health": {
            "console_logs_count": len(console_logs),
            "page_errors": page_errors,
            "failed_requests": failed_requests,
        },
        "screenshots": [
            "01_asset_vault_initial.png",
            "02_asset_uploaded.png",
            "03_watermark_config_modal.png",
            "04_embed_success.png",
            "05_vault_with_derivative.png",
            "06_verify_success_modal.png",
            "07_extract_payload_modal.png",
            "08_derivative_inspect_modal.png",
            "09_watermarked_filter_tab.png",
        ],
    }

    report_path = SCREENSHOTS_DIR / "acceptance_results.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[REPORT] Saved acceptance results to: {report_path}")
    print("\n=======================================================")
    print("  ALL REAL BROWSER ACCEPTANCE TESTS PASSED (100%)")
    print("=======================================================")


if __name__ == "__main__":
    run_browser_acceptance()
