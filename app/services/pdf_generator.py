from io import BytesIO
from PIL import Image, ImageOps
from app.config import config

class PDFGenerator:
    """
    Handles the high-resolution A4 PDF sheet generation.
    
    This service is responsible for calculating the optimal grid layout 
    for passport photos, handling multi-page overflows, and rendering 
    the final document at a professional print resolution (300 DPI).
    """
    
    def __init__(self, 
                 a4_w=config.A4_WIDTH, 
                 a4_h=config.A4_HEIGHT, 
                 margin_x=config.MARGIN_X, 
                 margin_y=config.MARGIN_Y, 
                 horizontal_gap=config.HORIZONTAL_GAP,
                 dpi=config.DEFAULT_DPI):
        """
        Initializes the generator with layout and resolution settings.
        """
        self.a4_w = a4_w
        self.a4_h = a4_h
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.horizontal_gap = horizontal_gap
        self.dpi = dpi

    def create_pdf_sheet(self, passport_images_with_copies, width, height, spacing, border):
        """
        Creates an A4 PDF sheet from processed images.
        
        Args:
            passport_images_with_copies (list): List of tuples (Image, copies).
            width (int): Target width of each photo in pixels.
            height (int): Target height of each photo in pixels.
            spacing (int): Vertical spacing between rows in pixels.
            border (int): Border thickness in pixels.
            
        Returns:
            BytesIO: A binary stream containing the generated PDF.
        """
        paste_w = width + 2 * border
        paste_h = height + 2 * border

        pages = []
        current_page = Image.new("RGB", (self.a4_w, self.a4_h), "white")
        x, y = self.margin_x, self.margin_y

        def new_page():
            nonlocal current_page, x, y
            pages.append(current_page)
            current_page = Image.new("RGB", (self.a4_w, self.a4_h), "white")
            x, y = self.margin_x, self.margin_y

        for original_img, copies in passport_images_with_copies:
            # Resize and add border
            with original_img.resize((width, height), Image.LANCZOS) as resized_img:
                with ImageOps.expand(resized_img, border=border, fill="black") as bordered_img:
                    for _ in range(copies):
                        # Check if we need a new row
                        if x + paste_w > self.a4_w - self.margin_x:
                            x = self.margin_x
                            y += paste_h + spacing

                        # Check if we need a new page
                        if y + paste_h > self.a4_h - self.margin_y:
                            new_page()

                        current_page.paste(bordered_img, (x, y))
                        x += paste_w + self.horizontal_gap

        pages.append(current_page)
        
        output = BytesIO()
        try:
            if len(pages) == 1:
                pages[0].save(output, format="PDF", dpi=(self.dpi, self.dpi))
            else:
                pages[0].save(
                    output,
                    format="PDF",
                    dpi=(self.dpi, self.dpi),
                    save_all=True,
                    append_images=pages[1:],
                )
            output.seek(0)
            return output
        finally:
            # Explicitly cleanup page images
            for page in pages:
                page.close()
