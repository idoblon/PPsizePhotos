import os
import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app
from app.config import config

app = create_app()

with app.app_context():
    print(f"REMOVE_BG_API_KEY present: {bool(config.REMOVE_BG_API_KEY)}")
    print(f"HAS_REMOVE_BG: {config.HAS_REMOVE_BG}")
    
    try:
        import rembg
        print("rembg is installed")
    except ImportError:
        print("rembg is NOT installed")
        
    try:
        import onnxruntime
        print("onnxruntime is installed")
    except ImportError:
        print("onnxruntime is NOT installed")

    u2net_home = os.environ.get("U2NET_HOME")
    print(f"U2NET_HOME: {u2net_home}")
    
    if u2net_home:
        print(f"U2NET_HOME exists: {os.path.exists(u2net_home)}")
        try:
            os.makedirs(u2net_home, exist_ok=True)
            print("Successfully checked/created U2NET_HOME directory")
        except Exception as e:
            print(f"Failed to create U2NET_HOME: {e}")
