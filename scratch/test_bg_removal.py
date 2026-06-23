import os
import sys
import logging
from pathlib import Path
from PIL import Image
from io import BytesIO

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.image_service import BackgroundRemovalStep
from app.config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bg_removal():
    print(f"Testing Background Removal...")
    print(f"REMOVE_BG_API_KEY configured: {config.HAS_REMOVE_BG}")
    
    # Create a simple test image (red square on white background)
    img = Image.new("RGB", (200, 200), color="red")
    
    # Initialize the step
    step = BackgroundRemovalStep()
    
    # Try processing
    print("Running process step...")
    try:
        result = step.process(img)
        print("Process completed.")
        
        # Check if it actually did anything (rembg returns transparency usually)
        # But ensure_rgb converts it back to RGB on white.
        # If it just returned the original image, size will be the same and pixels likely same.
        print(f"Result mode: {result.mode}")
        print(f"Result size: {result.size}")
        
    except Exception as e:
        print(f"Background removal failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test different U2NET_HOME settings
    original_u2net = os.environ.get("U2NET_HOME")
    print(f"Current U2NET_HOME: {original_u2net}")
    
    test_bg_removal()
