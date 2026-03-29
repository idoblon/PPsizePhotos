import requests
import cloudinary
import cloudinary.uploader
import cloudinary.utils
from PIL import Image, ImageOps
from io import BytesIO
from app.config import config
from app.exceptions import APIError, QuotaExceededError, FaceDetectionError, ImageProcessingError

class ImageService:
    @staticmethod
    def ensure_rgb(img: Image.Image) -> Image.Image:
        """Converts an image to RGB, handling transparency by pasting on a white background."""
        if img.mode in ("RGBA", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            return background
        return img.convert("RGB")

    @classmethod
    def remove_background(cls, input_image_bytes: bytes) -> Image.Image:
        """Calls Remove.bg API to remove background."""
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": input_image_bytes},
            data={"size": "auto"},
            headers={"X-Api-Key": config.REMOVE_BG_API_KEY},
        )

        if response.status_code != 200:
            cls._handle_api_error(response, "bg_removal")

        img = Image.open(BytesIO(response.content))
        return cls.ensure_rgb(img)

    @classmethod
    def enhance_image(cls, img: Image.Image) -> Image.Image:
        """Uploads to Cloudinary for AI enhancement and returns result."""
        cloudinary.config(
            cloud_name=config.CLOUDINARY_CLOUD_NAME,
            api_key=config.CLOUDINARY_API_KEY,
            api_secret=config.CLOUDINARY_API_SECRET,
        )
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        upload_result = cloudinary.uploader.upload(buffer, resource_type="image")
        public_id = upload_result.get("public_id")
        image_url = upload_result.get("secure_url")

        if not image_url:
            raise APIError("Cloudinary upload failed", status_code=500, error_code="cloudinary_upload_failed")

        # Step 3: Enhance via Cloudinary AI
        enhanced_url = cloudinary.utils.cloudinary_url(
            public_id,
            transformation=[
                {"effect": "gen_restore"},
                {"quality": "auto"},
                {"fetch_format": "auto"},
            ],
        )[0]

        enhanced_img_data = requests.get(enhanced_url).content
        enhanced_img = Image.open(BytesIO(enhanced_img_data))
        return cls.ensure_rgb(enhanced_img)

    @classmethod
    def process_single_image(cls, img_bytes: bytes) -> Image.Image:
        """Full pipeline: removal + enhancement."""
        img = cls.remove_background(img_bytes)
        img = cls.enhance_image(img)
        return img

    @staticmethod
    def _handle_api_error(response, context):
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

    @staticmethod
    def create_pdf_sheet(passport_images_with_copies, width, height, spacing, border):
        """Creates an A4 PDF sheet from processed images."""
        a4_w, a4_h = config.A4_WIDTH, config.A4_HEIGHT
        margin_x, margin_y = config.MARGIN_X, config.MARGIN_Y
        horizontal_gap = config.HORIZONTAL_GAP

        paste_w = width + 2 * border
        paste_h = height + 2 * border

        pages = []
        current_page = Image.new("RGB", (a4_w, a4_h), "white")
        x, y = margin_x, margin_y

        def new_page():
            nonlocal current_page, x, y
            pages.append(current_page)
            current_page = Image.new("RGB", (a4_w, a4_h), "white")
            x, y = margin_x, margin_y

        for img, copies in passport_images_with_copies:
            # Resize and add border here to keep the service method clean
            img = img.resize((width, height), Image.LANCZOS)
            img = ImageOps.expand(img, border=border, fill="black")
            
            for _ in range(copies):
                if x + paste_w > a4_w - margin_x:
                    x = margin_x
                    y += paste_h + spacing

                if y + paste_h > a4_h - margin_y:
                    new_page()

                current_page.paste(img, (x, y))
                x += paste_w + horizontal_gap

        pages.append(current_page)
        
        output = BytesIO()
        if len(pages) == 1:
            pages[0].save(output, format="PDF", dpi=(config.DEFAULT_DPI, config.DEFAULT_DPI))
        else:
            pages[0].save(
                output,
                format="PDF",
                dpi=(config.DEFAULT_DPI, config.DEFAULT_DPI),
                save_all=True,
                append_images=pages[1:],
            )
        output.seek(0)
        return output
