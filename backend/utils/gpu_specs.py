"""
GPU specifications loader and utilities
"""
import json
import logging
from typing import Dict, List, Optional
from config import Config

logger = logging.getLogger(__name__)

# Cache for GPU specs
_gpu_specs_cache: Optional[Dict] = None


def load_gpu_specs() -> Dict[str, Dict]:
    """Load GPU specifications from JSON file"""
    global _gpu_specs_cache

    if _gpu_specs_cache is not None:
        return _gpu_specs_cache

    try:
        with open(Config.GPU_SPECS_FILE, 'r') as f:
            data = json.load(f)
            # Convert list to dict keyed by GPU ID
            _gpu_specs_cache = {gpu['id']: gpu for gpu in data['gpus']}
            logger.info(f"Loaded {len(_gpu_specs_cache)} GPU specifications")
            return _gpu_specs_cache
    except Exception as e:
        logger.error(f"Failed to load GPU specs: {e}")
        return {}


def get_gpu_specs() -> Dict[str, Dict]:
    """Get all GPU specifications"""
    return load_gpu_specs()


def get_gpu_by_id(gpu_id: str) -> Optional[Dict]:
    """Get GPU specification by ID"""
    specs = get_gpu_specs()
    return specs.get(gpu_id)


def get_gpus_by_tier(tier: str) -> List[Dict]:
    """Get all GPUs of a specific tier"""
    specs = get_gpu_specs()
    return [gpu for gpu in specs.values() if gpu.get('tier') == tier]


def get_gpu_cost(gpu_id: str, interruptible: bool = True) -> float:
    """Get hourly cost for a GPU"""
    gpu = get_gpu_by_id(gpu_id)
    if not gpu:
        return 0.0

    base_cost = gpu.get('cost_per_hour', 0.0)
    if not interruptible:
        base_cost *= Config.SECURE_CLOUD_MULTIPLIER

    return base_cost


def format_gpu_info(gpu_id: str) -> str:
    """Format GPU information for display"""
    gpu = get_gpu_by_id(gpu_id)
    if not gpu:
        return f"Unknown GPU: {gpu_id}"

    return (
        f"{gpu['display_name']} "
        f"({gpu['vram_gb']}GB VRAM, "
        f"${gpu['cost_per_hour']:.2f}/hr)"
    )
