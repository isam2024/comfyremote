"""
Health check routes
"""
from flask import current_app, jsonify
from routes import health_bp
from config import Config
import logging

logger = logging.getLogger(__name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint

    Returns:
        JSON response with health status
    """
    pod_manager = current_app.config['POD_MANAGER']
    sse_broadcaster = current_app.config['SSE_BROADCASTER']

    active_pods = [p for p in pod_manager.list_pods() if p.status in ['running', 'initializing']]

    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'config': {
            'debug': Config.DEBUG,
            'api_key_set': bool(Config.RUNPOD_API_KEY),
        },
        'stats': {
            'total_pods': len(pod_manager.list_pods()),
            'active_pods': len(active_pods),
            'sse_clients': sse_broadcaster.get_client_count(),
        }
    }), 200


@health_bp.route('/gpus', methods=['GET'])
def list_gpus():
    """
    List available GPU types

    Returns:
        JSON response with GPU specifications
    """
    from utils.gpu_specs import get_gpu_specs

    specs = get_gpu_specs()

    # Convert to list and sort by cost
    gpu_list = list(specs.values())
    gpu_list.sort(key=lambda x: x.get('cost_per_hour', 0))

    return jsonify({
        'gpus': gpu_list,
        'count': len(gpu_list)
    }), 200
