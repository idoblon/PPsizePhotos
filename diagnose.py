"""Diagnose background removal on a real photo (uses 1 remove.bg credit).

Usage:
    python diagnose.py path/to/photo.jpg

Prints which engine ran, % of pixels removed, and saves
diagnose_bg_result.png so you can visually confirm the cutout.
"""
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from PIL import Image  # noqa: E402

from app.exceptions import APIError, FaceDetectionError, QuotaExceededError  # noqa: E402
from app.services.image_service import BackgroundRemovalStep  # noqa: E402


def main(path: str) -> int:
    step = BackgroundRemovalStep()
    key = (step.api_key or "").strip()
    print(f"API key present: {bool(key)}, length: {len(key) if key else 0}")
    if not key:
        print("No key -> server would use local AI only. Check .env then restart the server.")
        return 1

    img = Image.open(path)
    print(f"Input: {img.size} mode={img.mode}")

    try:
        out = step._process_via_api(img)
    except QuotaExceededError as e:
        print(f"QUOTA EXCEEDED: {e}")
        print("Top up credits at remove.bg dashboard.")
        return 2
    except FaceDetectionError as e:
        print(f"NO FACE/PERSON DETECTED: {e}")
        print("Try a photo with a clearly visible person, or skip tight cropping.")
        return 3
    except APIError as e:
        print(f"API ERROR (status {e.status_code}): {e}")
        return 4

    out.save("diagnose_bg_result.png")
    print(f"API OK. Output: {out.size} mode={out.mode} -> saved diagnose_bg_result.png")
    print("Open it: person on plain white = working. Original background still visible = API issue.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python diagnose.py path/to/photo.jpg")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
