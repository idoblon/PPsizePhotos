from flask import Blueprint, render_template, request, send_file, jsonify
from app.services.image_service import ImageService
from app.exceptions import AppError
import logging

main_bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)

@main_bp.route("/")
def index():
    return render_template("index.html")

@main_bp.route("/process", methods=["POST"])
def process():
    logger.info("Processing image request")
    
    try:
        # Layout settings
        width = int(request.form.get("width", 390))
        height = int(request.form.get("height", 480))
        border = int(request.form.get("border", 2))
        spacing = int(request.form.get("spacing", 10))
        
        images_data = []
        # Multi-image mode
        i = 0
        while f"image_{i}" in request.files:
            file = request.files[f"image_{i}"]
            copies = int(request.form.get(f"copies_{i}", 6))
            images_data.append((file.read(), copies))
            i += 1

        # Fallback to single image mode
        if not images_data and "image" in request.files:
            file = request.files["image"]
            copies = int(request.form.get("copies", 6))
            images_data.append((file.read(), copies))

        if not images_data:
            return jsonify({"error": "no_image_uploaded"}), 400

        passport_images = []
        for idx, (img_bytes, copies) in enumerate(images_data):
            logger.debug(f"Processing image {idx + 1}")
            # The service handles removal and enhancement
            img = ImageService.process_single_image(img_bytes)
            passport_images.append((img, copies))

        # Generate the PDF
        pdf_output = ImageService.create_pdf_sheet(
            passport_images, width, height, spacing, border
        )

        return send_file(
            pdf_output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="passport-sheet.pdf",
        )

    except AppError as e:
        logger.warning(f"Application error: {e.message}")
        return jsonify({"error": e.error_code, "message": e.message}), e.status_code
    except Exception as e:
        logger.exception("Unexpected error during processing")
        return jsonify({"error": "internal_error", "message": str(e)}), 500
