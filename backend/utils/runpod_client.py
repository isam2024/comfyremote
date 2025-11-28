"""
RunPod API client wrapper
Handles all interactions with the RunPod REST API
"""
import logging
import requests
from typing import Dict, Optional
from config import Config
from constants import RUNPOD_STATUS_MAP

logger = logging.getLogger(__name__)


class RunPodClient:
    """Client for RunPod REST API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.RUNPOD_API_KEY
        self.base_url = Config.RUNPOD_API_BASE
        self.timeout = Config.RUNPOD_API_TIMEOUT

        if not self.api_key:
            raise ValueError("RunPod API key is required")

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def create_pod(self, payload: Dict) -> Dict:
        """
        Create a new pod

        Args:
            payload: Pod creation payload

        Returns:
            Pod information dictionary

        Raises:
            requests.RequestException: If API call fails
        """
        url = f"{self.base_url}/pods"

        logger.info(f"Creating pod: {payload.get('name')}")
        logger.debug(f"Payload: {payload}")

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()
            pod_info = response.json()

            logger.info(f"Pod created successfully: {pod_info.get('id')}")
            return pod_info

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create pod: {e}")

            # Parse error response for more helpful message
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
                try:
                    error_data = e.response.json()
                    if 'error' in error_data:
                        runpod_error = error_data['error']
                        # Check for specific error types
                        if 'no instances currently available' in runpod_error.lower():
                            error_message = f"GPU not available: {payload.get('gpuTypeIds', ['Unknown'])[0]} has no available instances. Please try a different GPU type."
                        else:
                            error_message = f"RunPod error: {runpod_error}"
                except:
                    pass

            raise RuntimeError(error_message)

    def get_pod(self, pod_id: str) -> Dict:
        """
        Get pod information

        Args:
            pod_id: Pod ID

        Returns:
            Pod information dictionary

        Raises:
            requests.RequestException: If API call fails
        """
        url = f"{self.base_url}/pods/{pod_id}"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get pod {pod_id}: {e}")
            raise

    def list_pods(self) -> list:
        """
        List all pods

        Returns:
            List of pod information dictionaries

        Raises:
            requests.RequestException: If API call fails
        """
        url = f"{self.base_url}/pods"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            # API can return either a list directly or {pods: [...]}
            if isinstance(data, list):
                return data
            else:
                return data.get('pods', [])

        except requests.RequestException as e:
            logger.error(f"Failed to list pods: {e}")
            raise

    def terminate_pod(self, pod_id: str) -> bool:
        """
        Terminate a pod

        Args:
            pod_id: Pod ID

        Returns:
            True if successful

        Raises:
            requests.RequestException: If API call fails
        """
        url = f"{self.base_url}/pods/{pod_id}"

        logger.info(f"Terminating pod: {pod_id}")

        try:
            response = requests.delete(
                url,
                headers=self._get_headers(),
                timeout=30
            )

            # 204 No Content or 200 OK = success
            if response.status_code in [200, 204]:
                logger.info(f"Pod terminated successfully: {pod_id}")
                return True
            else:
                logger.error(f"Unexpected status code: {response.status_code}")
                response.raise_for_status()
                return False

        except requests.RequestException as e:
            logger.error(f"Failed to terminate pod {pod_id}: {e}")
            raise

    def get_pod_status(self, pod_id: str) -> str:
        """
        Get normalized pod status

        Args:
            pod_id: Pod ID

        Returns:
            Normalized status string

        Raises:
            requests.RequestException: If API call fails
        """
        pod_info = self.get_pod(pod_id)
        runpod_status = pod_info.get('desiredStatus', 'UNKNOWN').upper()

        # Map RunPod status to our status
        return RUNPOD_STATUS_MAP.get(runpod_status, 'unknown')

    def get_endpoint_url(self, pod_id: str, port: int, public_ip: bool = False) -> Optional[str]:
        """
        Get pod endpoint URL

        Args:
            pod_id: Pod ID
            port: Internal port number
            public_ip: Whether to use public IP (if available)

        Returns:
            Endpoint URL or None if not available
        """
        try:
            pod_info = self.get_pod(pod_id)

            if public_ip:
                # Try to get public IP mapping
                port_mappings = pod_info.get('portMappings', {})
                for mapping in port_mappings.values():
                    if mapping.get('internalPort') == port:
                        external_ip = mapping.get('externalIp')
                        external_port = mapping.get('externalPort')
                        if external_ip and external_port:
                            return f"http://{external_ip}:{external_port}"

            # Fallback to proxy URL
            return f"https://{pod_id}-{port}.proxy.runpod.net"

        except Exception as e:
            logger.error(f"Failed to get endpoint URL for pod {pod_id}: {e}")
            return None

    def wait_for_status(self, pod_id: str, target_status: str, timeout: int = 900) -> bool:
        """
        Wait for pod to reach target status

        Args:
            pod_id: Pod ID
            target_status: Target status to wait for
            timeout: Timeout in seconds

        Returns:
            True if target status reached, False if timeout
        """
        import time

        start_time = time.time()
        poll_interval = 10

        while (time.time() - start_time) < timeout:
            try:
                status = self.get_pod_status(pod_id)
                logger.debug(f"Pod {pod_id} status: {status}")

                if status == target_status:
                    return True

                if status in ['failed', 'stopped']:
                    logger.error(f"Pod {pod_id} entered terminal state: {status}")
                    return False

            except Exception as e:
                logger.warning(f"Error checking pod status: {e}")

            time.sleep(poll_interval)

        logger.error(f"Timeout waiting for pod {pod_id} to reach status {target_status}")
        return False

    def get_pod_logs(self, pod_id: str) -> Optional[Dict]:
        """
        Get pod logs

        Args:
            pod_id: Pod ID

        Returns:
            Logs response dictionary or None

        Raises:
            requests.RequestException: If API call fails
        """
        url = f"{self.base_url}/pods/{pod_id}/logs"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            logger.debug(f"Failed to get logs for pod {pod_id}: {e}")
            return None
