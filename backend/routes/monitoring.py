"""
Monitoring routes
Provides cost tracking and metrics
"""
from flask import current_app, jsonify, request
from routes import monitoring_bp
from constants import HTTP_OK, HTTP_NOT_FOUND, HTTP_INTERNAL_ERROR
import logging

logger = logging.getLogger(__name__)


@monitoring_bp.route('/cost/summary', methods=['GET'])
def get_cost_summary():
    """
    Get cost summary for all pods

    Returns:
        JSON response with cost summary
    """
    try:
        pod_manager = current_app.config['POD_MANAGER']
        cost_calculator = current_app.config['COST_CALCULATOR']

        pods = pod_manager.list_pods()
        summary = cost_calculator.get_cost_summary(pods)

        return jsonify(summary), HTTP_OK

    except Exception as e:
        logger.error(f"Error getting cost summary: {e}")
        return jsonify({'error': str(e)}), HTTP_INTERNAL_ERROR


@monitoring_bp.route('/cost/pod/<pod_id>', methods=['GET'])
def get_pod_cost(pod_id):
    """
    Get detailed cost information for a pod

    Args:
        pod_id: Pod ID

    Returns:
        JSON response with cost breakdown
    """
    try:
        pod_manager = current_app.config['POD_MANAGER']
        cost_calculator = current_app.config['COST_CALCULATOR']

        pod = pod_manager.get_pod(pod_id)

        if not pod:
            return jsonify({'error': 'Pod not found'}), HTTP_NOT_FOUND

        breakdown = cost_calculator.get_cost_breakdown(
            pod.gpu_id,
            pod.start_time,
            pod.config.interruptible
        )

        return jsonify(breakdown), HTTP_OK

    except Exception as e:
        logger.error(f"Error getting pod cost: {e}")
        return jsonify({'error': str(e)}), HTTP_INTERNAL_ERROR


@monitoring_bp.route('/estimate', methods=['POST'])
def estimate_cost():
    """
    Estimate cost for a configuration

    Request body:
        {
            "gpu_id": "NVIDIA GeForce RTX 4090",
            "hours": 24,
            "interruptible": true
        }

    Returns:
        JSON response with cost estimate
    """
    try:
        data = request.get_json()
        cost_calculator = current_app.config['COST_CALCULATOR']

        gpu_id = data.get('gpu_id')
        hours = data.get('hours', 1)
        interruptible = data.get('interruptible', True)

        if not gpu_id:
            return jsonify({'error': 'gpu_id is required'}), 400

        estimate = cost_calculator.estimate_cost(gpu_id, hours, interruptible)
        hourly_rate = cost_calculator.get_hourly_rate(gpu_id, interruptible)

        return jsonify({
            'gpu_id': gpu_id,
            'hours': hours,
            'interruptible': interruptible,
            'hourly_rate': hourly_rate,
            'estimated_cost': estimate,
        }), HTTP_OK

    except Exception as e:
        logger.error(f"Error estimating cost: {e}")
        return jsonify({'error': str(e)}), HTTP_INTERNAL_ERROR
