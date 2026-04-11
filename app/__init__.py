"""
Application Factory for Passport Photo Pro.
Initializes Flask, environment configuration, logging, and shared services.
"""

import os
import logging
import cloudinary
from flask import Flask
from app.config import config
from app.services.image_service import ImageService
from app.services.pdf_generator import PDFGenerator

def create_app():
    """
    Creates and configures the Flask application instance.
    
    1. Sets up centralized logging.
    2. Configures external services (Cloudinary).
    3. Initializes shared service instances (ImageService, PDFGenerator).
    4. Registers blueprints.
    
    Returns:
        Flask: The initialized Flask application.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, '..', 'templates')
    static_dir = os.path.join(base_dir, '..', 'static')

    app = Flask(__name__, 
                template_folder=template_dir, 
                static_folder=static_dir)
    
    # --- 1. Logging Setup ---
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # --- 2. Service Initialization ---
    # Configure Cloudinary globally if keys are available
    if config.HAS_CLOUDINARY:
        cloudinary.config(
            cloud_name=config.CLOUDINARY_CLOUD_NAME,
            api_key=config.CLOUDINARY_API_KEY,
            api_secret=config.CLOUDINARY_API_SECRET
        )
        logger.info("Cloudinary service initialized successfully.")
    else:
        logger.warning("Cloudinary keys missing. AI Enhancement will be skipped.")

    if not config.HAS_REMOVE_BG:
        logger.warning("Remove.bg API key missing. Background removal will be skipped.")

    # Initialize shared services and attach to the app object for easy access
    app.image_service = ImageService()
    app.pdf_generator = PDFGenerator()

    # --- 3. Route Registration ---
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
