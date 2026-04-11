import os
import logging
from pathlib import Path

# Load variables from .env if it exists in the project root
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)
if env_path.exists():
    logger.info(f"Loaded environment from {env_path}")
else:
    logger.info("Environment file not found; using system environment variables.")

class Config:
    """
    Base configuration containing default settings for the application.
    
    These values are shared across all environments unless overridden.
    """
    REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    
    # Feature Flags for Graceful Degradation
    HAS_REMOVE_BG = bool(REMOVE_BG_API_KEY)
    HAS_CLOUDINARY = bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET)
    
    # Layout Settings (DPI and Pixels)
    A4_WIDTH = 2480
    A4_HEIGHT = 3508
    DEFAULT_DPI = 300
    
    # Grid Defaults
    DEFAULT_PASSPORT_WIDTH = 390
    DEFAULT_PASSPORT_HEIGHT = 480
    DEFAULT_BORDER = 2
    DEFAULT_SPACING = 10
    MARGIN_X = 10
    MARGIN_Y = 10
    HORIZONTAL_GAP = 10

class DevelopmentConfig(Config):
    """Configuration for local development."""
    DEBUG = True

class ProductionConfig(Config):
    """Configuration for production environments."""
    DEBUG = False

# Mapping of environment names to config classes
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}

# The active config is selected based on the FLASK_ENV environment variable
config = config_map.get(os.getenv("FLASK_ENV", "production"), ProductionConfig)
