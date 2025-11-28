"""
Server-Sent Events (SSE) broadcaster
Manages SSE connections and broadcasts events to all connected clients
"""
import queue
import logging
import json
import time
from typing import List, Dict, Any, Optional
from constants import SSE_EVENT_CONNECTED

logger = logging.getLogger(__name__)


class SSEBroadcaster:
    """Manages SSE client connections and broadcasts events"""

    def __init__(self):
        self.clients: List[queue.Queue] = []
        logger.info("SSE Broadcaster initialized")

    def add_client(self) -> queue.Queue:
        """
        Add a new SSE client

        Returns:
            Queue for the client to receive messages
        """
        client_queue = queue.Queue(maxsize=100)
        self.clients.append(client_queue)
        logger.info(f"SSE client connected. Total clients: {len(self.clients)}")

        # Send connection confirmation
        self._send_to_client(client_queue, SSE_EVENT_CONNECTED, {
            'message': 'Connected to RunPod ComfyUI WebUI',
            'timestamp': time.time()
        })

        return client_queue

    def remove_client(self, client_queue: queue.Queue):
        """
        Remove an SSE client

        Args:
            client_queue: Client's message queue
        """
        if client_queue in self.clients:
            self.clients.remove(client_queue)
            logger.info(f"SSE client disconnected. Total clients: {len(self.clients)}")

    def broadcast(self, event_type: str, data: Dict[str, Any]):
        """
        Broadcast an event to all connected clients

        Args:
            event_type: Type of event (e.g., 'pod_status', 'cost_update')
            data: Event data dictionary
        """
        message = {
            'type': event_type,
            'data': data,
            'timestamp': time.time()
        }

        logger.debug(f"Broadcasting event: {event_type} to {len(self.clients)} clients")

        # Send to all clients
        dead_clients = []
        for client_queue in self.clients:
            try:
                client_queue.put_nowait(message)
            except queue.Full:
                logger.warning("Client queue full, removing slow client")
                dead_clients.append(client_queue)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                dead_clients.append(client_queue)

        # Clean up dead clients
        for dead_client in dead_clients:
            self.remove_client(dead_client)

    def _send_to_client(self, client_queue: queue.Queue, event_type: str, data: Dict[str, Any]):
        """
        Send event to a specific client

        Args:
            client_queue: Client's message queue
            event_type: Type of event
            data: Event data dictionary
        """
        message = {
            'type': event_type,
            'data': data,
            'timestamp': time.time()
        }

        try:
            client_queue.put_nowait(message)
        except queue.Full:
            logger.warning("Client queue full")
        except Exception as e:
            logger.error(f"Error sending to client: {e}")

    def get_client_count(self) -> int:
        """Get number of connected clients"""
        return len(self.clients)

    def broadcast_pod_status(self, pod_id: str, status: str, **kwargs):
        """
        Broadcast pod status update

        Args:
            pod_id: Pod ID
            status: Pod status
            **kwargs: Additional status data
        """
        data = {
            'pod_id': pod_id,
            'status': status,
            **kwargs
        }
        self.broadcast('pod_status', data)

    def broadcast_setup_progress(self, pod_id: str, step: str, percent: float, logs: List[str]):
        """
        Broadcast setup progress update

        Args:
            pod_id: Pod ID
            step: Current setup step
            percent: Progress percentage (0-100)
            logs: Setup log messages
        """
        data = {
            'pod_id': pod_id,
            'step': step,
            'percent': round(percent, 1),
            'logs': logs[-10:]  # Last 10 log lines
        }
        self.broadcast('setup_progress', data)

    def broadcast_cost_update(self, pod_id: str, cost_so_far: float, rate_per_hour: float):
        """
        Broadcast cost update

        Args:
            pod_id: Pod ID
            cost_so_far: Total cost accumulated so far
            rate_per_hour: Hourly cost rate
        """
        data = {
            'pod_id': pod_id,
            'cost_so_far': round(cost_so_far, 2),
            'rate_per_hour': round(rate_per_hour, 2)
        }
        self.broadcast('cost_update', data)

    def broadcast_pod_created(self, pod_id: str, name: str, gpu_id: str):
        """
        Broadcast pod creation event

        Args:
            pod_id: Pod ID
            name: Pod name
            gpu_id: GPU type ID
        """
        data = {
            'pod_id': pod_id,
            'name': name,
            'gpu_id': gpu_id
        }
        self.broadcast('pod_created', data)

    def broadcast_pod_terminated(self, pod_id: str):
        """
        Broadcast pod termination event

        Args:
            pod_id: Pod ID
        """
        data = {'pod_id': pod_id}
        self.broadcast('pod_terminated', data)

    def broadcast_error(self, error_message: str, pod_id: Optional[str] = None):
        """
        Broadcast error event

        Args:
            error_message: Error message
            pod_id: Optional pod ID if error is pod-specific
        """
        data = {
            'message': error_message,
            'pod_id': pod_id
        }
        self.broadcast('error', data)
