import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load local environment variables from .env file securely
load_dotenv(BASE_DIR / '.env')

class Config:
    """Application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'floodlens-dev-secret-key-2026-secure')
    
    # SQLite Database (normalized absolute path for cross-platform reliability)
    INSTANCE_DIR = BASE_DIR / 'instance'
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    db_file_path = (INSTANCE_DIR / 'floodlens.db').resolve().as_posix()
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URI', 
        f"sqlite:///{db_file_path}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Uploads
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tif', 'tiff', 'webp'}
    
    # Default Location: Chennai, Tamil Nadu, India
    DEFAULT_LAT = 13.0827
    DEFAULT_LON = 80.2707
    DEFAULT_LOCATION_NAME = "Chennai, Tamil Nadu, India"
    
    # Cache duration in seconds (5 minutes)
    CACHE_DURATION_SECONDS = 300
    
    # API Request Timeouts in seconds
    API_TIMEOUT = 10

