import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    
    # Layout Settings (Pixels)
    A4_WIDTH = 2480
    A4_HEIGHT = 3508
    DEFAULT_DPI = 300
    
    # Defaults
    DEFAULT_PASSPORT_WIDTH = 390
    DEFAULT_PASSPORT_HEIGHT = 480
    DEFAULT_BORDER = 2
    DEFAULT_SPACING = 10
    MARGIN_X = 10
    MARGIN_Y = 10
    HORIZONTAL_GAP = 10

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

# Select config based on environment variable if needed
config = DevelopmentConfig if os.getenv("FLASK_ENV") == "development" else ProductionConfig
