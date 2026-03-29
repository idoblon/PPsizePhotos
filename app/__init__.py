from flask import Flask
import logging
from app.config import config

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Register Blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
