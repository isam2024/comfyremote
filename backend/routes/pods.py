"""
Pod management routes
Handles pod creation, listing, and termination
"""
from flask import current_app, jsonify, request
from routes import pods_bp
from utils.validators import validate_create_pod_request
from constants import HTTP_OK, HTTP_CREATED, HTTP_BAD_REQUEST, HTTP_NOT_FOUND, HTTP_INTERNAL_ERROR
import logging

logger = logging.getLogger(__name__)


@pods_bp.route('', methods=['GET'])
def list_pods():
    """
    List all pods

    Returns:
        JSON response with list of pods
    """
    try:
        pod_manager = current_app.config['POD_MANAGER']
        cost_calculator = current_app.config['COST_CALCULATOR']

        pods = pod_manager.list_pods()

        # Convert to JSON
        pods_json = [pod.to_dict() for pod in pods]

        # Calculate total cost
        total_cost = cost_calculator.get_total_cost(pods)

        return jsonify({
            'pods': pods_json,
            'count': len(pods),
            'total_cost': total_cost
        }), HTTP_OK

    except Exception as e:
        logger.error(f"Error listing pods: {e}")
        return jsonify({'error': str(e)}), HTTP_INTERNAL_ERROR


@pods_bp.route('', methods=['POST'])
def create_pod():
    """
    Create a new pod

    Request body:
        {
            "name": "comfyui-pod",
            "gpu_id": "NVIDIA GeForce RTX 4090",
            "config": {
                "public_ip": false,
                "interruptible": true,
                "container_disk_gb": 70,
                "volume_disk_gb": 50,
                "models": [],
                "custom_nodes": [],
                "port": 8188
            }
        }

    Returns:
        JSON response with created pod
    """
    try:
        data = request.get_json()

        # Validate request
        valid, error = validate_create_pod_request(data)
        if not valid:
            return jsonify({'error': error}), HTTP_BAD_REQUEST

        pod_manager = current_app.config['POD_MANAGER']
        cost_calculator = current_app.config['COST_CALCULATOR']

        # Extract parameters
        name = data['name']
        gpu_id = data['gpu_id']
        config = data.get('config', {})

        # Create pod
        pod = pod_manager.create_pod(name, gpu_id, config)

        # Get cost estimate
        hourly_rate = cost_calculator.get_hourly_rate(gpu_id, pod.config.interruptible)

        response = pod.to_dict()
        response['hourly_rate'] = hourly_rate

        return jsonify(response), HTTP_CREATED

    except ValueError as e:
        logger.error(f"Validation error creating pod: {e}")
        return jsonify({'error': str(e)}), HTTP_BAD_REQUEST

    except RuntimeError as e:
        logger.error(f"Runtime error creating pod: {e}")
        return jsonify({'error': str(e)}), HTTP_INTERNAL_ERROR

    except Exception as e:
        logger.error(f"Unexpected error creating pod: {e}")
        return jsonify({'error': 'Internal server error'}), HTTP_INTERNAL_ERROR


@pods_bp.route('/<pod_id>', methods=['GET'])
def get_pod(pod_id):
    """
    Get pod details

    Args:
        pod_id: Pod ID

    Returns:
        JSON response with pod details
    """
    try:
        pod_manager = current_app.config['POD_MANAGER']
        cost_calculator = current_app.config['COST_CALCULATOR']

        pod = pod_manager.get_pod(pod_id)

        if not pod:
            return jsonify({'error': 'Pod not found'}), HTTP_NOT_FOUND

        # Get cost breakdown
        cost_breakdown = cost_calculator.get_cost_breakdown(
            pod.gpu_id,
            pod.start_time,
            pod.config.interruptible
        )

        response = pod.to_dict()
        response['cost_breakdown'] = cost_breakdown

        return jsonify(response), HTTP_OK

    except Exception as e:
        logger.error(f"Error getting pod {pod_id}: {e}")
        return jsonify({'error': str(e)}), HTTP_INTERNAL_ERROR


@pods_bp.route('/<pod_id>', methods=['DELETE'])
def terminate_pod(pod_id):
    """
    Terminate a pod

    Args:
        pod_id: Pod ID

    Returns:
        JSON response with termination status
    """
    try:
        pod_manager = current_app.config['POD_MANAGER']

        success = pod_manager.terminate_pod(pod_id)

        return jsonify({
            'success': success,
            'pod_id': pod_id,
            'message': 'Pod terminated successfully'
        }), HTTP_OK

    except ValueError as e:
        logger.error(f"Pod not found: {e}")
        return jsonify({'error': str(e)}), HTTP_NOT_FOUND

    except RuntimeError as e:
        logger.error(f"Error terminating pod: {e}")
        return jsonify({'error': str(e)}), HTTP_INTERNAL_ERROR

    except Exception as e:
        logger.error(f"Unexpected error terminating pod: {e}")
        return jsonify({'error': 'Internal server error'}), HTTP_INTERNAL_ERROR


@pods_bp.route('/<pod_id>/logs', methods=['GET'])
def get_pod_logs(pod_id):
    """
    Get pod setup logs

    Args:
        pod_id: Pod ID

    Returns:
        JSON response with logs
    """
    try:
        pod_manager = current_app.config['POD_MANAGER']

        pod = pod_manager.get_pod(pod_id)

        if not pod:
            return jsonify({'error': 'Pod not found'}), HTTP_NOT_FOUND

        return jsonify({
            'pod_id': pod_id,
            'logs': pod.setup_logs,
            'status': pod.status,
            'progress': pod.setup_progress
        }), HTTP_OK

    except Exception as e:
        logger.error(f"Error getting pod logs: {e}")
        return jsonify({'error': str(e)}), HTTP_INTERNAL_ERROR
