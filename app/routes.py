"""
Main routing logic for the Passport Photo Pro application.
Handles incoming user requests for image processing and sheet generation.
"""

from flask import Blueprint, render_template, request, send_file, jsonify, current_app
from app.exceptions import AppError
from app.utils.validators import RequestValidator
import logging

# Define the main blueprint
main_bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)

@main_bp.route("/")
def index():
    """Renders the main application UI."""
    return render_template("index.html")

@main_bp.route("/status")
def status():
    """Diagnostic endpoint to verify API key detection."""
    from app.config import config
    return jsonify({
        "services": {
            "remove_bg": {
                "enabled": config.HAS_REMOVE_BG,
                "key_present": bool(config.REMOVE_BG_API_KEY)
            },
            "cloudinary": {
                "enabled": config.HAS_CLOUDINARY,
                "cloud_name_present": bool(config.CLOUDINARY_CLOUD_NAME),
                "api_key_present": bool(config.CLOUDINARY_API_KEY),
                "api_secret_present": bool(config.CLOUDINARY_API_SECRET)
            }
        },
        "environment": current_app.config.get("ENV", "not_set")
    })

@main_bp.route("/process", methods=["POST"])
def process():
    """
    Main endpoint for photo processing and A4 sheet generation.
    
    1. Validates incoming form parameters and image files.
    2. Runs each image through the enhancement pipeline.
    3. Generates a high-resolution A4 PDF document.
    
    Returns:
        Response: A binary PDF file for download or a JSON error object.
    """
    logger.info("Processing image request")
    
    try:
        # Phase 3: Input Validation
        # Safely parse and validate form data/files
        validated = RequestValidator.validate_process_request(request.form, request.files)
        
        passport_images = []
        for img_file, copies in validated['images_data']:
            logger.debug(f"Processing image: {img_file.filename}")
            
            # The service handles removal and enhancement through the pipeline
            # Note: The raw bytes are read here, ensure the image service closes its internal handles
            img_bytes = img_file.read()
            processed_img = current_app.image_service.process_single_image(img_bytes)
            passport_images.append((processed_img, copies))

        # Generate the PDF using the dedicated generator
        pdf_output = current_app.pdf_generator.create_pdf_sheet(
            passport_images, 
            validated['width'], 
            validated['height'], 
            validated['spacing'], 
            validated['border']
        )

        return send_file(
            pdf_output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="passport-sheet.pdf"
        )

    except AppError as e:
        logger.warning(f"Application error: {e.message} (Code: {e.error_code})")
        return jsonify({"error": e.error_code, "message": e.message}), e.status_code
    except Exception as e:
        logger.exception("Unexpected error during processing")
        return jsonify({"error": "internal_error", "message": "An unexpected server error occurred."}), 500
