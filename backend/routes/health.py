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


@health_bp.route('/gpus/check-availability', methods=['POST'])
def check_gpu_availability():
    """
    Check if a specific GPU is available

    Request body:
        {
            "gpu_id": str,
            "interruptible": bool (optional, default True)
        }

    Returns:
        JSON response with availability status and alternatives
    """
    from flask import request
    from utils.gpu_specs import get_gpu_specs, get_gpu_cost

    data = request.get_json()
    if not data or 'gpu_id' not in data:
        return jsonify({
            'error': 'gpu_id is required'
        }), 400

    gpu_id = data['gpu_id']
    interruptible = data.get('interruptible', True)

    # Get RunPod client
    pod_manager = current_app.config['POD_MANAGER']
    runpod_client = pod_manager.runpod_client

    # Check availability
    availability = runpod_client.check_gpu_availability(gpu_id)

    # Build response message
    if availability['available']:
        cloud_type = []
        if availability['community_available']:
            cloud_type.append('Community Cloud')
        if availability['secure_available']:
            cloud_type.append('Secure Cloud')

        message = f"{gpu_id} is available in {' and '.join(cloud_type)}"
    else:
        message = f"{gpu_id} is currently unavailable. Please select an alternative GPU."

    # If not available, suggest alternatives
    alternatives = []
    if not availability['available']:
        specs = get_gpu_specs()
        requested_gpu = specs.get(gpu_id)

        if requested_gpu:
            requested_cost = requested_gpu.get('cost_per_hour', 0)

            # Find similar GPUs by cost (±30% price range)
            similar_gpus = []
            for spec_id, spec in specs.items():
                if spec_id == gpu_id:
                    continue

                spec_cost = spec.get('cost_per_hour', 0)
                cost_diff = abs(spec_cost - requested_cost)
                cost_ratio = cost_diff / requested_cost if requested_cost > 0 else 1

                if cost_ratio <= 0.3:  # Within 30% of requested price
                    # Check if this one is available
                    alt_availability = runpod_client.check_gpu_availability(spec_id)
                    if alt_availability['available']:
                        similar_gpus.append({
                            'gpu_id': spec_id,
                            'name': spec.get('name', spec_id),
                            'cost_per_hour': spec_cost,
                            'vram': spec.get('vram', 'N/A'),
                            'community_available': alt_availability['community_available'],
                            'secure_available': alt_availability['secure_available'],
                            'cost_diff': round(spec_cost - requested_cost, 2)
                        })

            # Sort by cost difference (closest to requested price first)
            similar_gpus.sort(key=lambda x: abs(x['cost_diff']))
            alternatives = similar_gpus[:5]  # Return top 5 alternatives

    return jsonify({
        'available': availability['available'],
        'gpu_id': gpu_id,
        'community_available': availability['community_available'],
        'secure_available': availability['secure_available'],
        'message': message,
        'alternatives': alternatives
    }), 200
