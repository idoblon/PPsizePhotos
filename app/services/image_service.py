import os
import requests
import cloudinary
import cloudinary.uploader
import cloudinary.utils
import logging
from PIL import Image
from io import BytesIO
from abc import ABC, abstractmethod
from app.config import config
from app.exceptions import APIError, QuotaExceededError, FaceDetectionError

logger = logging.getLogger(__name__)

# Configure rembg to use /tmp for model storage (required for Vercel/Serverless)
os.environ["U2NET_HOME"] = os.path.join("/tmp", ".u2net")

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
            error_msg = error_info.get("errors", [{}])[0].get("message", "unknown_error")
            error_code = error_info.get("errors", [{}])[0].get("code", "unknown_error")
            
            if response.status_code == 429:
                raise QuotaExceededError(f"{context} quota exceeded: {error_msg}")
            if response.status_code == 410 or "face" in error_msg.lower():
                raise FaceDetectionError(f"{context} face detection failed: {error_msg}")
            
            raise APIError(f"{context} failed: {error_msg}", status_code=response.status_code, error_code=error_code)
        except Exception as e:
            if isinstance(e, (QuotaExceededError, FaceDetectionError, APIError)):
                raise
            raise APIError(f"{context} unknown error", status_code=response.status_code)

class BackgroundRemovalStep(ProcessStep):
    """
    Primary background removal step using Remove.bg API, 
    with a graceful fallback to local AI if API is unavailable.
    """
    def __init__(self, api_key=config.REMOVE_BG_API_KEY):
        self.api_key = api_key

    def process(self, img: Image.Image) -> Image.Image:
        # 1. Try Professional API first (Highest Quality)
        if config.HAS_REMOVE_BG:
            try:
                logger.info("Attempting Background Removal via Remove.bg API...")
                return self._process_via_api(img)
            except Exception as e:
                logger.error(f"Remove.bg API failed: {e}. Falling back to local AI.")
        
        # 2. Fallback to Local AI (Autonomous & Free)
        logger.info("Using Local AI (rembg) for background removal...")
        return self._process_locally(img)

    def _process_via_api(self, img: Image.Image) -> Image.Image:
        with BytesIO() as buffer:
            img.save(buffer, format="PNG")
            buffer.seek(0)

            response = requests.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": buffer},
                data={"size": "auto"},
                headers={"X-Api-Key": self.api_key},
                timeout=15
            )

        if response.status_code != 200:
            self._handle_api_error(response, "bg_removal")

        with Image.open(BytesIO(response.content)) as result_img:
            return self.ensure_rgb(result_img)

    def _process_locally(self, img: Image.Image) -> Image.Image:
        """Performs background removal using the rembg library."""
        try:
            from rembg import remove, new_session
            
            # Using u2netp (portable) model for better performance in serverless envs
            session = new_session("u2netp")
            
            # rembg returns an RGBA image
            result_rgba = remove(img, session=session)
            return self.ensure_rgb(result_rgba)
        except Exception as e:
            logger.error(f"Local background removal failed: {e}")
            # If everything fails, return the original RGB image as last resort
            return self.ensure_rgb(img)

class EnhancementStep(ProcessStep):
    """Utilizes Cloudinary's AI enhancement."""
    def __init__(self, 
                 cloud_name=config.CLOUDINARY_CLOUD_NAME,
                 api_key=config.CLOUDINARY_API_KEY,
                 api_secret=config.CLOUDINARY_API_SECRET):
        self.config = {
            "cloud_name": cloud_name,
            "api_key": api_key,
            "api_secret": api_secret
        }

    def process(self, img: Image.Image) -> Image.Image:
        if not config.HAS_CLOUDINARY:
            logger.warning("Enhancement skipped: Cloudinary keys not configured.")
            return img

        cloudinary.config(**self.config)
        with BytesIO() as buffer:
            img.save(buffer, format="PNG")
            buffer.seek(0)
            upload_result = cloudinary.uploader.upload(buffer, resource_type="image")
            
        public_id = upload_result.get("public_id")
        image_url = upload_result.get("secure_url")

        if not image_url:
            raise APIError("Cloudinary upload failed", status_code=500)

        enhanced_url = cloudinary.utils.cloudinary_url(
            public_id,
            transformation=[{"effect": "gen_restore"}, {"quality": "auto"}]
        )[0]

        enhanced_img_data = requests.get(enhanced_url, timeout=15).content
        with Image.open(BytesIO(enhanced_img_data)) as enhanced_img:
            return self.ensure_rgb(enhanced_img)

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
