import unittest
from unittest.mock import MagicMock, patch
from io import BytesIO
from PIL import Image
from app.services.image_service import ImageService, ProcessStep, BackgroundRemovalStep, EnhancementStep
from app.services.pdf_generator import PDFGenerator

class TestRefactoring(unittest.TestCase):
    def setUp(self):
        # Create a dummy image
        self.img = Image.new("RGB", (100, 100), color="red")
        self.img_bytes = BytesIO()
        self.img.save(self.img_bytes, format="PNG")
        self.img_bytes = self.img_bytes.getvalue()

    @patch("app.services.image_service.requests.post")
    def test_background_removal_step(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Return a simple white image as the result
        result_img = Image.new("RGB", (100, 100), color="white")
        buf = BytesIO()
        result_img.save(buf, format="PNG")
        mock_response.content = buf.getvalue()
        mock_post.return_value = mock_response

        step = BackgroundRemovalStep(api_key="fake_key")
        result = step.process(self.img)
        
        self.assertEqual(result.size, (100, 100))
        # Check if the pixel at (0,0) is white (255, 255, 255)
        self.assertEqual(result.getpixel((0,0)), (255, 255, 255))

    @patch("app.services.image_service.cloudinary.uploader.upload")
    @patch("app.services.image_service.cloudinary.utils.cloudinary_url")
    @patch("app.services.image_service.requests.get")
    def test_enhancement_step(self, mock_get, mock_url, mock_upload):
        mock_upload.return_value = {"public_id": "test_id", "secure_url": "http://test.url"}
        mock_url.return_value = ("http://enhanced.url", {})
        
        mock_response = MagicMock()
        enhanced_img = Image.new("RGB", (100, 100), color="blue")
        buf = BytesIO()
        enhanced_img.save(buf, format="PNG")
        mock_response.content = buf.getvalue()
        mock_get.return_value = mock_response

        step = EnhancementStep(cloud_name="n", api_key="k", api_secret="s")
        result = step.process(self.img)

        self.assertEqual(result.getpixel((0,0)), (0, 0, 255))

    def test_pdf_generator_layout(self):
        gen = PDFGenerator(a4_w=200, a4_h=200, margin_x=10, margin_y=10, horizontal_gap=5)
        # 10x10 image, 2 copies
        img = Image.new("RGB", (10, 10), color="green")
        pdf_buf = gen.create_pdf_sheet([(img, 2)], width=10, height=10, spacing=5, border=0)
        
        self.assertIsInstance(pdf_buf, BytesIO)
        # Check if PDF header is present
        self.assertTrue(pdf_buf.getvalue().startswith(b"%PDF"))

if __name__ == "__main__":
    unittest.main()
