"""
Configuration management for RunPod ComfyUI WebUI
Loads settings from environment variables with sensible defaults
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration"""

    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '1445'))

    # RunPod Configuration
    RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY', '')
    RUNPOD_API_BASE = 'https://rest.runpod.io/v1'
    RUNPOD_API_TIMEOUT = int(os.getenv('RUNPOD_API_TIMEOUT', '800'))

    # ComfyUI Configuration
    COMFYUI_PORT = int(os.getenv('COMFYUI_PORT', '8188'))
    COMFYUI_IMAGE = os.getenv('COMFYUI_IMAGE', 'runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04')

    # File Paths
    BASE_DIR = Path(__file__).parent
    PROJECT_ROOT = BASE_DIR.parent
    DATA_DIR = PROJECT_ROOT / 'data'
    GPU_SPECS_FILE = DATA_DIR / 'gpu_specs.json'

    # Pod Defaults
    DEFAULT_CONTAINER_DISK_GB = 70
    DEFAULT_VOLUME_DISK_GB = 50
    DEFAULT_GPU_ID = "NVIDIA GeForce RTX 3070"
    DEFAULT_CLOUD_TYPE = "COMMUNITY"  # COMMUNITY or SECURE

    # SSE Configuration
    SSE_KEEPALIVE_INTERVAL = 30  # seconds
    SSE_RETRY_TIMEOUT = 3000  # milliseconds

    # Cost Tracking
    COST_UPDATE_INTERVAL = 60  # seconds
    SECURE_CLOUD_MULTIPLIER = 2.0  # Secure cloud costs 2x community cloud

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []

        if not cls.RUNPOD_API_KEY:
            errors.append("RUNPOD_API_KEY environment variable is required")

        if not cls.GPU_SPECS_FILE.exists():
            errors.append(f"GPU specs file not found: {cls.GPU_SPECS_FILE}")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        return True

    @classmethod
    def get_summary(cls):
        """Get configuration summary for logging"""
        return {
            'debug': cls.DEBUG,
            'host': cls.HOST,
            'port': cls.PORT,
            'api_key_set': bool(cls.RUNPOD_API_KEY),
            'gpu_specs_exists': cls.GPU_SPECS_FILE.exists(),
        }
