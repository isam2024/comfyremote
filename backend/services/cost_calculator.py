"""
Cost calculation service
Calculates and tracks costs for RunPod instances
"""
import logging
from datetime import datetime
from typing import Dict
from utils.gpu_specs import get_gpu_cost
from config import Config

logger = logging.getLogger(__name__)


class CostCalculator:
    """Service for calculating pod costs"""

    def __init__(self):
        logger.info("CostCalculator initialized")

    def calculate_cost(self, gpu_id: str, start_time: datetime, interruptible: bool = True) -> float:
        """
        Calculate accumulated cost for a pod

        Args:
            gpu_id: GPU type ID
            start_time: Pod start timestamp
            interruptible: Whether using interruptible (community cloud) pricing

        Returns:
            Total cost in USD
        """
        # Get hourly rate
        hourly_rate = get_gpu_cost(gpu_id, interruptible)

        # Calculate elapsed time in hours
        # Use utcnow() since RunPod timestamps are in UTC
        elapsed = datetime.utcnow() - start_time
        elapsed_hours = elapsed.total_seconds() / 3600.0

        # Calculate total cost
        total_cost = elapsed_hours * hourly_rate

        return round(total_cost, 4)

    def get_hourly_rate(self, gpu_id: str, interruptible: bool = True) -> float:
        """
        Get hourly rate for a GPU

        Args:
            gpu_id: GPU type ID
            interruptible: Whether using interruptible pricing

        Returns:
            Hourly rate in USD
        """
        return get_gpu_cost(gpu_id, interruptible)

    def estimate_cost(self, gpu_id: str, hours: float, interruptible: bool = True) -> float:
        """
        Estimate cost for a given duration

        Args:
            gpu_id: GPU type ID
            hours: Duration in hours
            interruptible: Whether using interruptible pricing

        Returns:
            Estimated cost in USD
        """
        hourly_rate = self.get_hourly_rate(gpu_id, interruptible)
        return round(hourly_rate * hours, 2)

    def get_cost_breakdown(self, gpu_id: str, start_time: datetime, interruptible: bool = True) -> Dict:
        """
        Get detailed cost breakdown

        Args:
            gpu_id: GPU type ID
            start_time: Pod start timestamp
            interruptible: Whether using interruptible pricing

        Returns:
            Dictionary with cost breakdown
        """
        hourly_rate = self.get_hourly_rate(gpu_id, interruptible)
        elapsed = datetime.now() - start_time
        elapsed_hours = elapsed.total_seconds() / 3600.0
        total_cost = self.calculate_cost(gpu_id, start_time, interruptible)

        # Project costs
        cost_24h = hourly_rate * 24
        cost_7d = hourly_rate * 24 * 7
        cost_30d = hourly_rate * 24 * 30

        return {
            'hourly_rate': round(hourly_rate, 4),
            'elapsed_hours': round(elapsed_hours, 2),
            'total_cost': round(total_cost, 2),
            'interruptible': interruptible,
            'cloud_type': 'Community Cloud' if interruptible else 'Secure Cloud',
            'projections': {
                '24_hours': round(cost_24h, 2),
                '7_days': round(cost_7d, 2),
                '30_days': round(cost_30d, 2),
            }
        }

    def get_total_cost(self, pods: list) -> float:
        """
        Calculate total cost across multiple pods

        Args:
            pods: List of pod objects with gpu_id, start_time, and config

        Returns:
            Total cost in USD
        """
        total = 0.0

        for pod in pods:
            # For running/initializing pods, calculate real-time cost
            if pod.status in ['running', 'initializing'] and pod.start_time:
                cost = self.calculate_cost(
                    pod.gpu_id,
                    pod.start_time,
                    pod.config.interruptible
                )
                total += cost
            # For stopped/terminated pods, use the pre-calculated cost
            elif hasattr(pod, 'cost_so_far'):
                total += pod.cost_so_far

        return round(total, 2)

    def format_cost(self, cost: float) -> str:
        """
        Format cost for display

        Args:
            cost: Cost in USD

        Returns:
            Formatted cost string
        """
        return f"${cost:.2f}"

    def get_cost_summary(self, pods: list) -> Dict:
        """
        Get cost summary for all pods

        Args:
            pods: List of pod objects

        Returns:
            Cost summary dictionary
        """
        total_cost = self.get_total_cost(pods)

        # Group by GPU type
        by_gpu = {}
        for pod in pods:
            # Calculate cost based on pod status
            if pod.status in ['running', 'initializing'] and pod.start_time:
                cost = self.calculate_cost(
                    pod.gpu_id,
                    pod.start_time,
                    pod.config.interruptible
                )
            elif hasattr(pod, 'cost_so_far'):
                cost = pod.cost_so_far
            else:
                continue

            if pod.gpu_id not in by_gpu:
                by_gpu[pod.gpu_id] = {
                    'count': 0,
                    'cost': 0.0,
                }

            by_gpu[pod.gpu_id]['count'] += 1
            by_gpu[pod.gpu_id]['cost'] += cost

        # Round costs
        for gpu_id in by_gpu:
            by_gpu[gpu_id]['cost'] = round(by_gpu[gpu_id]['cost'], 2)

        return {
            'total_cost': total_cost,
            'total_pods': len(pods),
            'by_gpu': by_gpu,
        }
