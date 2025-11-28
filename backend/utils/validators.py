"""
Input validation utilities
"""
import logging
from typing import Dict, List, Optional, Tuple
from utils.gpu_specs import get_gpu_by_id
from constants import POD_STATUSES

logger = logging.getLogger(__name__)


def validate_gpu_id(gpu_id: str) -> Tuple[bool, Optional[str]]:
    """Validate GPU ID exists in specs"""
    gpu = get_gpu_by_id(gpu_id)
    if not gpu:
        return False, f"Invalid GPU ID: {gpu_id}"
    return True, None


def validate_pod_config(config: Dict) -> Tuple[bool, Optional[str]]:
    """Validate pod configuration"""
    errors = []

    # Validate container disk size
    container_disk = config.get('container_disk_gb', 70)
    if not isinstance(container_disk, int) or container_disk < 50 or container_disk > 500:
        errors.append("container_disk_gb must be between 50 and 500")

    # Validate volume disk size
    volume_disk = config.get('volume_disk_gb', 50)
    if not isinstance(volume_disk, int) or volume_disk < 1 or volume_disk > 1000:
        errors.append("volume_disk_gb must be between 1 and 1000")

    # Validate port
    port = config.get('port', 8188)
    if not isinstance(port, int) or port < 1024 or port > 65535:
        errors.append("port must be between 1024 and 65535")

    # Validate boolean fields
    if 'public_ip' in config and not isinstance(config['public_ip'], bool):
        errors.append("public_ip must be a boolean")

    if 'interruptible' in config and not isinstance(config['interruptible'], bool):
        errors.append("interruptible must be a boolean")

    # Validate lists
    if 'models' in config and not isinstance(config['models'], list):
        errors.append("models must be a list")

    if 'custom_nodes' in config and not isinstance(config['custom_nodes'], list):
        errors.append("custom_nodes must be a list")

    if errors:
        return False, "; ".join(errors)

    return True, None


def validate_pod_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate pod name"""
    if not name or not isinstance(name, str):
        return False, "Pod name is required and must be a string"

    if len(name) < 3 or len(name) > 50:
        return False, "Pod name must be between 3 and 50 characters"

    # Allow alphanumeric, hyphens, and underscores
    if not all(c.isalnum() or c in '-_' for c in name):
        return False, "Pod name can only contain letters, numbers, hyphens, and underscores"

    return True, None


def validate_pod_status(status: str) -> Tuple[bool, Optional[str]]:
    """Validate pod status"""
    if status not in POD_STATUSES:
        return False, f"Invalid status. Must be one of: {', '.join(POD_STATUSES)}"
    return True, None


def validate_create_pod_request(data: Dict) -> Tuple[bool, Optional[str]]:
    """Validate complete pod creation request"""
    errors = []

    # Required fields
    if 'name' not in data:
        errors.append("name is required")
    else:
        valid, error = validate_pod_name(data['name'])
        if not valid:
            errors.append(error)

    if 'gpu_id' not in data:
        errors.append("gpu_id is required")
    else:
        valid, error = validate_gpu_id(data['gpu_id'])
        if not valid:
            errors.append(error)

    # Optional config validation
    if 'config' in data:
        valid, error = validate_pod_config(data['config'])
        if not valid:
            errors.append(f"Invalid config: {error}")

    if errors:
        return False, "; ".join(errors)

    return True, None
