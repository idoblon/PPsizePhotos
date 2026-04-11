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

class ProcessStep(ABC):
    """
    Abstract base class for an image processing step in the pipeline.
    
    Subclasses must implement the `process` method to perform specific 
    transformations on an Image object.
    """
    @abstractmethod
    def process(self, img: Image.Image) -> Image.Image:
        """
        Processes the input image and returns the transformed result.
        
        Args:
            img (PIL.Image.Image): The input image to process.
            
        Returns:
            PIL.Image.Image: The processed image.
        """
        pass

    @staticmethod
    def ensure_rgb(img: Image.Image) -> Image.Image:
        """
        Converts an image to RGB mode, handling transparency gracefully.
        
        If the image is in RA/LA mode, it pastes the image onto a white 
        background to preserve visual consistency after transparency is removed.
        
        Args:
            img (PIL.Image.Image): The input image.
            
        Returns:
            PIL.Image.Image: The RGB converted image.
        """
        if img.mode in ("RGBA", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            return background
        return img.convert("RGB")

    def _handle_api_error(self, response, context):
        """
        Standardizes error handling for external API calls.
        
        Args:
            response (requests.Response): The response from the external API.
            context (str): A description of the operation (e.g., "bg_removal").
            
        Raises:
            QuotaExceededError: If the API returns a 429 status.
            FaceDetectionError: If a face could not be detected in the image.
            APIError: For other non-200 API responses.
        """
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
    Step that utilizes the Remove.bg API to isolate the subject from the background.
    """
    def __init__(self, api_key=config.REMOVE_BG_API_KEY):
        """
        Initializes the step with a Remove.bg API key.
        """
        self.api_key = api_key

    def process(self, img: Image.Image) -> Image.Image:
        """
        Performs background removal using the Remove.bg service.
        
        If the service is not configured (missing API key), it logs a warning 
         and returns the original image.
        """
        if not config.HAS_REMOVE_BG:
            logger.warning(f"Background removal skipped: REMOVE_BG_API_KEY NOT found. (HAS_REMOVE_BG={config.HAS_REMOVE_BG})")
            return img
        
        logger.info("Executing BackgroundRemovalStep...")

        with BytesIO() as buffer:
            img.save(buffer, format="PNG")
            buffer.seek(0)

            response = requests.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": buffer},
                data={"size": "auto"},
                headers={"X-Api-Key": self.api_key},
            )

        if response.status_code != 200:
            self._handle_api_error(response, "bg_removal")

        with Image.open(BytesIO(response.content)) as result_img:
            return self.ensure_rgb(result_img)

class EnhancementStep(ProcessStep):
    """
    Step that utilizes Cloudinary's AI 'gen_restore' effect to enhance image quality.
    """
    def __init__(self, 
                 cloud_name=config.CLOUDINARY_CLOUD_NAME,
                 api_key=config.CLOUDINARY_API_KEY,
                 api_secret=config.CLOUDINARY_API_SECRET):
        """
        Initializes the step with Cloudinary credentials.
        """
        self.config = {
            "cloud_name": cloud_name,
            "api_key": api_key,
            "api_secret": api_secret
        }

    def process(self, img: Image.Image) -> Image.Image:
        """
        Uploads the image to Cloudinary, applies AI enhancement, and returns the result.
        
        If Cloudinary is not configured, it logs a warning and returns the original image.
        """
        if not config.HAS_CLOUDINARY:
            logger.warning("Image enhancement skipped: Cloudinary keys not configured.")
            return img

        cloudinary.config(**self.config)
        
        with BytesIO() as buffer:
            img.save(buffer, format="PNG")
            buffer.seek(0)
            
            upload_result = cloudinary.uploader.upload(buffer, resource_type="image")
            
        public_id = upload_result.get("public_id")
        image_url = upload_result.get("secure_url")

        if not image_url:
            raise APIError("Cloudinary upload failed", status_code=500, error_code="cloudinary_upload_failed")

        enhanced_url = cloudinary.utils.cloudinary_url(
            public_id,
            transformation=[
                {"effect": "gen_restore"},
                {"quality": "auto"},
                {"fetch_format": "auto"},
            ],
        )[0]

        enhanced_img_data = requests.get(enhanced_url).content
        with Image.open(BytesIO(enhanced_img_data)) as enhanced_img:
            return self.ensure_rgb(enhanced_img)

class ImageService:
    """
    Orchestrates the image processing pipeline by running an image through 
    successive transformation steps.
    """
    
    def __init__(self, steps=None):
        """
        Initializes the service with a list of processing steps.
        
        If no steps are provided, it defaults to a standard pipeline of 
        background removal followed by AI enhancement.
        """
        if steps is None:
            self.steps = [
                BackgroundRemovalStep(),
                EnhancementStep()
            ]
        else:
            self.steps = steps

    def process_single_image(self, img_bytes: bytes) -> Image.Image:
        """
        Executes the full processing pipeline on raw image bytes.
        
        Args:
            img_bytes (bytes): The raw bytes of the uploaded image.
            
        Returns:
            PIL.Image.Image: The fully processed, RGB-converted image.
        """
        with Image.open(BytesIO(img_bytes)) as img:
            # Ensure initial RGB conversion if needed
            if img.mode not in ("RGB", "RGBA"):
                img = self.steps[0].ensure_rgb(img) if self.steps else img.convert("RGB")

            processed_img = img
            for step in self.steps:
                processed_img = step.process(processed_img)
            
            # Ensure the image data is fully loaded and survives the context manager
            processed_img.load()
            return processed_img.copy()
