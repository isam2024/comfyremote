"""
Route blueprints for RunPod ComfyUI WebUI
"""
from flask import Blueprint

# Initialize blueprints
pods_bp = Blueprint('pods', __name__, url_prefix='/api/pods')
sse_bp = Blueprint('sse', __name__, url_prefix='/api/stream')
monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/monitoring')
health_bp = Blueprint('health', __name__, url_prefix='/api')
workflows_bp = Blueprint('workflows', __name__, url_prefix='/api/workflows')

# Import routes to register them with blueprints
from . import pods, sse, monitoring, health, workflows

__all__ = ['pods_bp', 'sse_bp', 'monitoring_bp', 'health_bp', 'workflows_bp']
