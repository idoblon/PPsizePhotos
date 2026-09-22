import os
import requests
import cloudinary
import cloudinary.uploader
import cloudinary.utils
import logging
import tempfile
from PIL import Image
from io import BytesIO
from abc import ABC, abstractmethod
from flask import g, has_request_context
from app.config import config
from app.exceptions import APIError, QuotaExceededError, FaceDetectionError

logger = logging.getLogger(__name__)

# Model cache dir: /tmp on serverless, OS temp dir elsewhere (Windows-safe).
# Respect a pre-set U2NET_HOME; never overwrite an explicit user setting.
os.environ.setdefault("U2NET_HOME", os.path.join(tempfile.gettempdir(), ".u2net"))


def _note_bg_method(name: str) -> None:
    """Records which bg-removal path ran, for the X-Bg-Removal response header."""
    if has_request_context():
        methods = getattr(g, "bg_methods", None)
        if methods is None:
            methods = g.bg_methods = []
        if name not in methods:
            methods.append(name)

class ProcessStep(ABC):
    """
    Abstract base class for an image processing step in the pipeline.
    """
    @abstractmethod
    def process(self, img: Image.Image) -> Image.Image:
        pass

    @staticmethod
    def ensure_rgb(img: Image.Image) -> Image.Image:
        """Converts an image to RGB mode, handling transparency gracefully."""
        if img.mode in ("RGBA", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            return background
        return img.convert("RGB")

    def _handle_api_error(self, response, context):
        try:
            error_info = response.json()
        except Exception:
            raise APIError(f"{context} failed with status {response.status_code}", status_code=response.status_code)

        error_msg = error_info.get("errors", [{}])[0].get("message", "unknown_error")
        error_code = error_info.get("errors", [{}])[0].get("code", "unknown_error")

        if response.status_code == 429:
            raise QuotaExceededError(f"{context} quota exceeded: {error_msg}")
        if response.status_code == 402:
            raise QuotaExceededError(f"{context} out of credits (HTTP 402): {error_msg}")
        if response.status_code == 410 or "face" in error_msg.lower():
            raise FaceDetectionError(f"{context} face detection failed: {error_msg}")

        raise APIError(f"{context} failed: {error_msg}", status_code=response.status_code, error_code=error_code)

class BackgroundRemovalStep(ProcessStep):
    """
    Primary background removal step using Remove.bg API,
    with a graceful fallback to local AI if API is unavailable.
    """
    _rembg_session = None

    def __init__(self, api_key=None):
        # Resolve at runtime (not import time) so env changes / tests work
        self.api_key = api_key or config.REMOVE_BG_API_KEY

    def process(self, img: Image.Image) -> Image.Image:
        # 1. Try Professional API first (Highest Quality)
        if self.api_key:
            try:
                logger.info("Attempting Background Removal via Remove.bg API...")
                result = self._process_via_api(img)
                _note_bg_method("removebg-api")
                return result
            except Exception as e:
                logger.error(f"Remove.bg API failed: {e}. Falling back to local AI.")
                _note_bg_method("local-ai-fallback")
        else:
            logger.warning("Remove.bg API key missing; using local AI only.")
            _note_bg_method("local-ai")

        # 2. Fallback to Local AI (Autonomous & Free)
        logger.info("Using Local AI (rembg) for background removal...")
        return self._process_locally(img)

    @staticmethod
    def _removed_ratio(rgba_img: Image.Image) -> float:
        """Fraction of pixels the model marked as background (0.0-1.0)."""
        try:
            alpha = rgba_img.split()[-1]
            hist = alpha.histogram()
            transparent = sum(hist[:128])
            total = rgba_img.size[0] * rgba_img.size[1]
            return transparent / total if total else 0.0
        except Exception:
            return 0.0

    def _warn_if_nothing_removed(self, rgba_img: Image.Image, source: str) -> None:
        ratio = self._removed_ratio(rgba_img)
        logger.info(f"Background removal ({source}): {ratio:.1%} of pixels removed.")
        if ratio < 0.005:
            logger.warning(
                f"Background removal ({source}) removed almost nothing "
                f"({ratio:.1%}). The photo may have no detectable person, "
                "or the model failed — output will look like the original."
            )

    def _process_via_api(self, img: Image.Image) -> Image.Image:
        with BytesIO() as buffer:
            img.save(buffer, format="PNG")
            buffer.seek(0)

            response = requests.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": ("image.png", buffer, "image/png")},
                data={"size": "auto"},
                headers={"X-Api-Key": self.api_key},
                timeout=15
            )

        if response.status_code != 200:
            self._handle_api_error(response, "bg_removal")

        with Image.open(BytesIO(response.content)) as result_img:
            result_img.load()
            if result_img.mode in ("RGBA", "LA"):
                self._warn_if_nothing_removed(result_img, "removebg-api")
            return self.ensure_rgb(result_img)

    def _process_locally(self, img: Image.Image) -> Image.Image:
        """Performs background removal using the rembg library."""
        try:
            from rembg import remove, new_session

            if BackgroundRemovalStep._rembg_session is None:
                logger.info("Initializing rembg session (u2netp)...")
                BackgroundRemovalStep._rembg_session = new_session("u2netp")

            result_rgba = remove(img, session=BackgroundRemovalStep._rembg_session)
            self._warn_if_nothing_removed(result_rgba, "local-ai")
            return self.ensure_rgb(result_rgba)
        except Exception as e:
            logger.error(f"Local background removal failed: {e}")
            return self.ensure_rgb(img)

class EnhancementStep(ProcessStep):
    """Utilizes Cloudinary's AI enhancement."""
    def __init__(self,
                 cloud_name=None,
                 api_key=None,
                 api_secret=None):
        # Resolve at runtime so injected test creds / late env vars work
        self.config = {
            "cloud_name": cloud_name or config.CLOUDINARY_CLOUD_NAME,
            "api_key": api_key or config.CLOUDINARY_API_KEY,
            "api_secret": api_secret or config.CLOUDINARY_API_SECRET,
        }

    def is_enabled(self) -> bool:
        return bool(
            self.config.get("cloud_name")
            and self.config.get("api_key")
            and self.config.get("api_secret")
        )

    def process(self, img: Image.Image) -> Image.Image:
        if not self.is_enabled():
            logger.warning("Enhancement skipped: Cloudinary keys not configured.")
            return img

        public_id = None
        try:
            cloudinary.config(**self.config)
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            upload_result = cloudinary.uploader.upload(buffer, resource_type="image")

            public_id = upload_result.get("public_id")
            if not public_id:
                raise APIError("Cloudinary upload failed: no public_id returned", status_code=500)

            enhanced_url = cloudinary.utils.cloudinary_url(
                public_id,
                transformation=[{"effect": "gen_restore"}, {"quality": "auto"}]
            )[0]

            enhanced_img_data = requests.get(enhanced_url, timeout=15).content
            with Image.open(BytesIO(enhanced_img_data)) as enhanced_img:
                return self.ensure_rgb(enhanced_img)
        except Exception as e:
            logger.error(f"Cloudinary enhancement failed: {e}. Returning image without enhancement.")
            return img
        finally:
            if public_id:
                try:
                    cloudinary.uploader.destroy(public_id)
                except Exception as cleanup_err:
                    logger.warning(f"Failed to delete Cloudinary asset '{public_id}': {cleanup_err}")

class ImageService:
    """Orchestrates the image processing pipeline."""
    def __init__(self, steps=None):
        if steps is None:
            self.steps = [BackgroundRemovalStep(), EnhancementStep()]
        else:
            self.steps = steps

    def process_single_image(self, img_bytes: bytes) -> Image.Image:
        with Image.open(BytesIO(img_bytes)) as img:
            # Ensure fixed orientation and mode
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
            
            processed_img = img
            for step in self.steps:
                processed_img = step.process(processed_img)
            
            # Ensure the image data is fully loaded and survives the context manager
            processed_img.load()
            return processed_img.copy()
