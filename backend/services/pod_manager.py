"""
Pod Manager Service
Manages ComfyUI pod lifecycle: creation, monitoring, termination
"""
import logging
import threading
import time
from typing import Dict, Optional, List
from datetime import datetime

from models import Pod, PodConfig
from utils.runpod_client import RunPodClient
from utils.gpu_specs import get_gpu_by_id
from services.sse_broadcaster import SSEBroadcaster
from services.cost_calculator import CostCalculator
from config import Config
from constants import (
    POD_STATUS_INITIALIZING,
    POD_STATUS_RUNNING,
    POD_STATUS_FAILED,
    POD_STATUS_STOPPED,
    POD_STATUS_TERMINATED,
    DEFAULT_MODELS,
    DEFAULT_CUSTOM_NODES,
    MODEL_URLS,
)

logger = logging.getLogger(__name__)


class PodManager:
    """Manages ComfyUI pods"""

    def __init__(self, sse_broadcaster: Optional[SSEBroadcaster] = None):
        self.pods: Dict[str, Pod] = {}
        self.runpod_client = RunPodClient()
        self.sse_broadcaster = sse_broadcaster or SSEBroadcaster()
        self.cost_calculator = CostCalculator()
        self._monitoring_thread = None
        self._stop_monitoring = False

        logger.info("PodManager initialized")

        # Sync existing pods from RunPod
        self._sync_from_runpod()

        # Start background monitoring
        self._start_monitoring()

    def create_pod(self, name: str, gpu_id: str, config: Optional[Dict] = None) -> Pod:
        """
        Create a new ComfyUI pod

        Args:
            name: Pod name
            gpu_id: GPU type ID
            config: Optional pod configuration

        Returns:
            Pod object

        Raises:
            ValueError: If validation fails
            RuntimeError: If pod creation fails
        """
        logger.info(f"Creating pod: {name} with GPU: {gpu_id}")

        # Parse config
        pod_config = PodConfig.from_dict(config or {})

        # Build ComfyUI setup script
        docker_cmd = self._build_comfyui_setup_script(pod_config)

        # Build RunPod API payload
        payload = self._build_runpod_payload(name, gpu_id, pod_config, docker_cmd)

        # Create pod via RunPod API
        try:
            pod_info = self.runpod_client.create_pod(payload)
            pod_id = pod_info.get('id')

            if not pod_id:
                raise RuntimeError("Pod creation failed: no pod ID returned")

            # Calculate hourly rate
            from utils.gpu_specs import get_gpu_cost
            hourly_rate = get_gpu_cost(gpu_id, pod_config.interruptible)

            # Get actual creation time from RunPod API (convert from UTC string)
            created_at_str = pod_info.get('createdAt', '')
            if created_at_str:
                # Parse RunPod's UTC timestamp format: "2025-11-27 17:56:21.701466089 +0000 UTC"
                start_time = datetime.strptime(created_at_str.replace(' +0000 UTC', ''), '%Y-%m-%d %H:%M:%S.%f')
            else:
                start_time = datetime.now()

            # Create pod object
            pod = Pod(
                pod_id=pod_id,
                name=name,
                gpu_id=gpu_id,
                config=pod_config,
                status=POD_STATUS_INITIALIZING,
                start_time=start_time,
                hourly_rate=hourly_rate,
            )

            # Store pod
            self.pods[pod_id] = pod

            # Broadcast creation event
            if self.sse_broadcaster:
                self.sse_broadcaster.broadcast_pod_created(pod_id, name, gpu_id)

            logger.info(f"Pod created successfully: {pod_id}")

            # Start monitoring thread for this pod
            self._start_pod_setup_monitor(pod)

            return pod

        except Exception as e:
            logger.error(f"Failed to create pod: {e}")
            raise RuntimeError(f"Pod creation failed: {str(e)}")

    def _build_comfyui_setup_script(self, config: PodConfig) -> str:
        """
        Build the Docker startup script for ComfyUI installation

        Args:
            config: Pod configuration

        Returns:
            Bash script as string
        """
        port = config.port

        # Determine which models to download
        models = config.models if config.models else list(DEFAULT_MODELS['diffusion'])
        clip_models = DEFAULT_MODELS['clip']
        vae_models = DEFAULT_MODELS['vae']
        lora_models = DEFAULT_MODELS['loras']

        # Determine custom nodes
        custom_nodes = config.custom_nodes if config.custom_nodes else DEFAULT_CUSTOM_NODES

        # Build download commands for diffusion models
        model_downloads = []
        for model in models:
            url = MODEL_URLS.get(model, '')
            if url:
                model_downloads.append(
                    f"[ -f {model} ] || sudo -E -u comfyui curl -L -o {model} {url}"
                )

        # Build clip downloads
        clip_downloads = []
        for model in clip_models:
            url = MODEL_URLS.get(model, '')
            if url:
                clip_downloads.append(
                    f"[ -f {model} ] || sudo -E -u comfyui curl -L -o {model} {url}"
                )

        # Build VAE downloads
        vae_downloads = []
        for model in vae_models:
            url = MODEL_URLS.get(model, '')
            if url:
                vae_downloads.append(
                    f"[ -f {model} ] || sudo -E -u comfyui curl -L -o {model} {url}"
                )

        # Build LoRA downloads
        lora_downloads = []
        for model in lora_models:
            url = MODEL_URLS.get(model, '')
            if url:
                lora_downloads.append(
                    f"[ -f {model} ] || sudo -E -u comfyui curl -L -o {model} {url}"
                )

        # Build custom node clones
        custom_node_installs = []
        for node_url in custom_nodes:
            repo_name = node_url.split('/')[-1].replace('.git', '')
            custom_node_installs.append(
                f"sudo -E -u comfyui git clone {node_url} || true"
            )

        script = f"""
set -e

# Install basic tools
apt-get update && apt-get install -y git wget curl python3 python3-pip sudo

# Create non-root user
id -u comfyui &>/dev/null || useradd -m -s /bin/bash comfyui

# Setup directory structure
mkdir -p /opt/ComfyUI
chown -R comfyui:comfyui /opt/ComfyUI
export HOME=/home/comfyui
export COMFYUI_ALLOW_ROOT=1
export PATH=/home/comfyui/.local/bin:$PATH

# Clone ComfyUI
if [ ! -d /opt/ComfyUI/.git ]; then
    sudo -E -u comfyui git clone https://github.com/comfyanonymous/ComfyUI /opt/ComfyUI
fi

# Install dependencies
cd /opt/ComfyUI
python3 -m pip install --upgrade pip
pip install pyyaml
pip install -r requirements.txt

# Create model directories
mkdir -p models/diffusion_models models/clip models/vae models/loras

# Download diffusion models
cd models/diffusion_models
{chr(10).join(model_downloads)}

# Download CLIP models
cd ../clip
{chr(10).join(clip_downloads)}

# Download VAE models
cd ../vae
{chr(10).join(vae_downloads)}

# Download LoRA models
cd ../loras
{chr(10).join(lora_downloads)}

# Setup custom nodes
mkdir -p /opt/ComfyUI/custom_nodes
cd /opt/ComfyUI/custom_nodes
{chr(10).join(custom_node_installs)}

# Install custom node requirements
for node_dir in /opt/ComfyUI/custom_nodes/*/; do
    if [ -f "${{node_dir}}requirements.txt" ]; then
        cd "$node_dir"
        pip install -r requirements.txt || true
    fi
done

# Launch ComfyUI
cd /opt/ComfyUI
sudo -E -u comfyui python3 main.py --listen 0.0.0.0 --port {port}
"""

        return script.strip()

    def _build_runpod_payload(self, name: str, gpu_id: str, config: PodConfig, docker_cmd: str) -> Dict:
        """
        Build RunPod API payload

        Args:
            name: Pod name
            gpu_id: GPU type ID
            config: Pod configuration
            docker_cmd: Docker startup command

        Returns:
            API payload dictionary
        """
        # Determine ports configuration
        if config.public_ip:
            ports = [f"{config.port}/tcp", "22/tcp"]
        else:
            ports = [f"{config.port}/http", "22/tcp"]

        # Determine cloud type
        cloud_type = Config.DEFAULT_CLOUD_TYPE if config.interruptible else "SECURE"

        payload = {
            "name": name,
            "imageName": Config.COMFYUI_IMAGE,
            "computeType": "GPU",
            "gpuTypeIds": [gpu_id],
            "gpuTypePriority": "availability",
            "gpuCount": 1,
            "vcpuCount": 2,
            "volumeInGb": config.volume_disk_gb,
            "volumeMountPath": "/workspace",
            "containerDiskInGb": config.container_disk_gb,
            "ports": ports,
            "supportPublicIp": config.public_ip,
            "cloudType": cloud_type,
            "dockerStartCmd": ["/bin/bash", "-c", docker_cmd],
        }

        return payload

    def _start_pod_setup_monitor(self, pod: Pod):
        """
        Start background thread to monitor pod setup

        Args:
            pod: Pod object
        """
        def monitor():
            try:
                last_log_count = 0
                start_time = time.time()

                # Monitor setup progress
                while True:
                    # Check if we've exceeded timeout (15 minutes)
                    if time.time() - start_time > 900:
                        pod.status = POD_STATUS_FAILED
                        pod.error_message = "Pod setup timeout (15 minutes)"
                        pod.add_log("✗ Setup failed: timeout")

                        if self.sse_broadcaster:
                            self.sse_broadcaster.broadcast_pod_status(
                                pod.pod_id,
                                POD_STATUS_FAILED,
                                error=pod.error_message
                            )
                        break

                    # Get current pod status
                    try:
                        pod_info = self.runpod_client.get_pod(pod.pod_id)
                        current_status = pod_info.get('desiredStatus', 'PENDING')

                        # Get logs to show progress
                        logs_response = self.runpod_client.get_pod_logs(pod.pod_id)
                        if logs_response and 'logs' in logs_response:
                            logs = logs_response['logs']

                            # Add new log lines
                            if len(logs) > last_log_count:
                                new_logs = logs[last_log_count:]
                                for log_entry in new_logs:
                                    log_line = log_entry.get('line', '').strip()
                                    if log_line:
                                        pod.add_log(log_line)

                                last_log_count = len(logs)

                                # Estimate progress based on log content
                                progress = self._estimate_setup_progress(pod.setup_logs)
                                pod.setup_progress = progress

                                # Broadcast progress update
                                if self.sse_broadcaster:
                                    self.sse_broadcaster.broadcast_setup_progress(
                                        pod.pod_id,
                                        "Installing",
                                        progress,
                                        pod.setup_logs[-10:]  # Last 10 logs
                                    )

                        # Check if pod is running
                        if current_status == 'RUNNING':
                            # Get endpoint URL
                            endpoint_url = self.runpod_client.get_endpoint_url(
                                pod.pod_id,
                                pod.config.port,
                                pod.config.public_ip
                            )
                            pod.endpoint_url = endpoint_url

                            # Verify ComfyUI is actually accessible
                            try:
                                import requests
                                response = requests.get(endpoint_url, timeout=10)
                                if response.status_code == 200:
                                    # ComfyUI is truly ready!
                                    pod.status = POD_STATUS_RUNNING
                                    pod.setup_progress = 100.0
                                    pod.add_log("✓ ComfyUI is running!")
                                    pod.add_log(f"✓ Endpoint: {endpoint_url}")

                                    # Broadcast status update
                                    if self.sse_broadcaster:
                                        self.sse_broadcaster.broadcast_pod_status(
                                            pod.pod_id,
                                            POD_STATUS_RUNNING,
                                            endpoint_url=endpoint_url,
                                            uptime=pod.get_uptime_formatted()
                                        )
                                    break
                                else:
                                    # Container running but ComfyUI not ready yet
                                    pod.setup_progress = min(pod.setup_progress + 5, 95)
                                    logger.debug(f"Pod {pod.pod_id} container running, waiting for ComfyUI (HTTP {response.status_code})...")
                            except Exception as e:
                                # Endpoint not accessible yet - keep monitoring
                                pod.setup_progress = min(pod.setup_progress + 5, 95)
                                logger.debug(f"Pod {pod.pod_id} container running, waiting for ComfyUI endpoint...")

                    except Exception as log_error:
                        logger.debug(f"Error fetching logs: {log_error}")

                    # Wait before next poll
                    time.sleep(5)

            except Exception as e:
                logger.error(f"Error monitoring pod setup: {e}")
                pod.status = POD_STATUS_FAILED
                pod.error_message = str(e)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def _estimate_setup_progress(self, logs: List[str]) -> float:
        """
        Estimate setup progress based on log content

        Args:
            logs: List of log lines

        Returns:
            Progress percentage (0-100)
        """
        if not logs:
            return 5.0

        progress = 10.0  # Base progress
        log_text = ' '.join(logs).lower()

        # Milestone-based progress estimation
        if 'installing' in log_text or 'install' in log_text:
            progress = max(progress, 20.0)
        if 'cloning' in log_text or 'clone' in log_text:
            progress = max(progress, 30.0)
        if 'downloading' in log_text or 'download' in log_text:
            progress = max(progress, 40.0)
        if 'model' in log_text:
            progress = max(progress, 60.0)
        if 'comfyui' in log_text and 'running' in log_text:
            progress = max(progress, 90.0)

        return min(progress, 95.0)  # Cap at 95% until confirmed running

    def get_pod(self, pod_id: str) -> Optional[Pod]:
        """
        Get pod by ID

        Args:
            pod_id: Pod ID

        Returns:
            Pod object or None
        """
        return self.pods.get(pod_id)

    def list_pods(self) -> List[Pod]:
        """
        List all pods

        Returns:
            List of Pod objects
        """
        return list(self.pods.values())

    def resume_pod(self, pod_id: str) -> bool:
        """
        Resume a stopped pod

        Args:
            pod_id: Pod ID

        Returns:
            True if successful

        Raises:
            ValueError: If pod not found
            RuntimeError: If resume fails
        """
        pod = self.get_pod(pod_id)
        if not pod:
            raise ValueError(f"Pod not found: {pod_id}")

        logger.info(f"Resuming pod: {pod_id}")

        try:
            # Resume via RunPod API
            success = self.runpod_client.resume_pod(pod_id)

            if success:
                # Update pod status
                pod.status = POD_STATUS_INITIALIZING
                pod.add_log("Pod resuming...")

                # Broadcast status update
                if self.sse_broadcaster:
                    self.sse_broadcaster.broadcast_pod_status(
                        pod_id,
                        POD_STATUS_INITIALIZING
                    )

                # Start monitoring setup again
                self._start_pod_setup_monitor(pod)

                logger.info(f"Pod resumed successfully: {pod_id}")
                return True
            else:
                raise RuntimeError("Resume failed")

        except Exception as e:
            logger.error(f"Failed to resume pod {pod_id}: {e}")
            raise RuntimeError(f"Resume failed: {str(e)}")

    def terminate_pod(self, pod_id: str) -> bool:
        """
        Terminate a pod

        Args:
            pod_id: Pod ID

        Returns:
            True if successful

        Raises:
            ValueError: If pod not found
            RuntimeError: If termination fails
        """
        pod = self.get_pod(pod_id)
        if not pod:
            raise ValueError(f"Pod not found: {pod_id}")

        logger.info(f"Terminating pod: {pod_id}")

        try:
            # Terminate via RunPod API
            success = self.runpod_client.terminate_pod(pod_id)

            if success:
                # Update pod status
                pod.status = POD_STATUS_TERMINATED
                pod.add_log("Pod terminated")

                # Broadcast termination
                if self.sse_broadcaster:
                    self.sse_broadcaster.broadcast_pod_terminated(pod_id)

                # Remove from tracking (optional - keep for history)
                # del self.pods[pod_id]

                logger.info(f"Pod terminated successfully: {pod_id}")
                return True
            else:
                raise RuntimeError("Termination failed")

        except Exception as e:
            logger.error(f"Failed to terminate pod {pod_id}: {e}")
            raise RuntimeError(f"Termination failed: {str(e)}")

    def _sync_from_runpod(self):
        """
        Sync existing pods from RunPod on startup
        """
        try:
            logger.info("Syncing pods from RunPod...")
            runpod_pods = self.runpod_client.list_pods()

            for pod_info in runpod_pods:
                pod_id = pod_info.get('id')
                if not pod_id:
                    continue

                # Skip if we already have this pod
                if pod_id in self.pods:
                    continue

                # Reconstruct pod object from RunPod data
                name = pod_info.get('name', f'pod-{pod_id[:8]}')

                # Get cost per hour from RunPod
                cost_per_hour = float(pod_info.get('costPerHr', 0))

                # Try to get GPU from machine info or gpuTypeIds
                gpu_id = 'Unknown'
                if pod_info.get('gpuTypeIds'):
                    gpu_id = pod_info.get('gpuTypeIds')[0]
                elif pod_info.get('machine', {}).get('gpuDisplayName'):
                    gpu_id = pod_info['machine']['gpuDisplayName']
                else:
                    # Try fetching individual pod details for GPU info
                    try:
                        detailed_info = self.runpod_client.get_pod(pod_id)
                        if detailed_info.get('gpuTypeIds'):
                            gpu_id = detailed_info['gpuTypeIds'][0]
                        elif detailed_info.get('machine', {}).get('gpuDisplayName'):
                            gpu_id = detailed_info['machine']['gpuDisplayName']
                    except:
                        pass

                    # If still unknown, try to infer from cost
                    if gpu_id == 'Unknown' and cost_per_hour > 0:
                        # Try to match cost to GPU specs
                        gpu_spec = get_gpu_by_id(None, cost_per_hour=cost_per_hour)
                        if gpu_spec:
                            gpu_id = gpu_spec['id']

                # Map RunPod status to our status
                runpod_status = pod_info.get('desiredStatus', 'UNKNOWN').upper()
                status_map = {
                    'RUNNING': POD_STATUS_RUNNING,
                    'EXITED': POD_STATUS_STOPPED,
                    'FAILED': POD_STATUS_FAILED,
                    'PENDING': POD_STATUS_INITIALIZING,
                }
                status = status_map.get(runpod_status, POD_STATUS_STOPPED)

                # Parse timestamps to calculate runtime cost
                created_at_str = pod_info.get('createdAt')
                start_time = datetime.now()
                if created_at_str:
                    try:
                        # Parse RunPod timestamp: "2025-11-28 01:17:13.837 +0000 UTC"
                        created_at_str = created_at_str.replace(' +0000 UTC', '')
                        start_time = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S.%f')
                    except:
                        pass

                # Calculate cost based on runtime
                cost_so_far = 0.0
                if status in [POD_STATUS_RUNNING, POD_STATUS_INITIALIZING]:
                    runtime_hours = (datetime.now() - start_time).total_seconds() / 3600
                    cost_so_far = runtime_hours * cost_per_hour
                elif status in [POD_STATUS_STOPPED, POD_STATUS_TERMINATED]:
                    # For stopped pods, try to get runtime from lastStartedAt to lastStatusChange
                    last_started = pod_info.get('lastStartedAt')
                    last_status_change = pod_info.get('lastStatusChange')
                    if last_started:
                        try:
                            last_started = last_started.replace(' +0000 UTC', '')
                            started = datetime.strptime(last_started, '%Y-%m-%d %H:%M:%S.%f')
                            # For stopped pods, use start time
                            start_time = started
                            # Estimate runtime (rough calculation)
                            runtime_hours = 0.1  # Minimum charge
                            cost_so_far = runtime_hours * cost_per_hour
                        except:
                            pass

                # Create minimal pod config (we don't have full config from RunPod)
                pod_config = PodConfig()

                # Create pod object
                pod = Pod(
                    pod_id=pod_id,
                    name=name,
                    gpu_id=gpu_id,
                    config=pod_config,
                    status=status,
                    start_time=start_time,
                )

                # Set hourly rate and cost
                pod.hourly_rate = cost_per_hour
                pod.cost_so_far = cost_so_far

                # Get endpoint URL if running
                if status == POD_STATUS_RUNNING:
                    endpoint_url = self.runpod_client.get_endpoint_url(
                        pod_id,
                        pod_config.port,
                        pod_config.public_ip
                    )
                    pod.endpoint_url = endpoint_url

                    # Check if ComfyUI is actually accessible
                    # If not, pod is still setting up - start monitoring
                    try:
                        import requests
                        response = requests.get(endpoint_url, timeout=5)
                        if response.status_code == 200:
                            # ComfyUI is running
                            pod.setup_progress = 100.0
                            pod.add_log("✓ ComfyUI is running!")
                        else:
                            # Container running but ComfyUI not ready yet
                            pod.status = POD_STATUS_INITIALIZING
                            pod.setup_progress = 50.0  # Container started
                            pod.add_log("Container started, setting up ComfyUI...")
                    except:
                        # Endpoint not accessible - still setting up
                        pod.status = POD_STATUS_INITIALIZING
                        pod.setup_progress = 50.0
                        pod.add_log("Container started, setting up ComfyUI...")

                # Add to our tracking
                self.pods[pod_id] = pod
                logger.info(f"Synced pod from RunPod: {pod_id} ({name}) - {status}")

                # Start monitoring for pods that are still setting up
                if pod.status == POD_STATUS_INITIALIZING:
                    logger.info(f"Starting setup monitor for synced pod: {pod_id}")
                    self._start_pod_setup_monitor(pod)

            logger.info(f"Sync complete: {len(runpod_pods)} pods restored from RunPod")

        except Exception as e:
            logger.error(f"Failed to sync pods from RunPod: {e}")
            # Don't fail startup if sync fails

    def _start_monitoring(self):
        """Start background monitoring thread"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return

        def monitor_loop():
            logger.info("Starting pod monitoring loop")

            while not self._stop_monitoring:
                try:
                    # Update costs and heartbeats
                    for pod in self.pods.values():
                        if pod.status in [POD_STATUS_RUNNING, POD_STATUS_INITIALIZING]:
                            # Update cost
                            pod.cost_so_far = self.cost_calculator.calculate_cost(
                                pod.gpu_id,
                                pod.start_time,
                                pod.config.interruptible
                            )

                            # Broadcast cost update
                            if self.sse_broadcaster:
                                hourly_rate = self.cost_calculator.get_hourly_rate(
                                    pod.gpu_id,
                                    pod.config.interruptible
                                )
                                self.sse_broadcaster.broadcast_cost_update(
                                    pod.pod_id,
                                    pod.cost_so_far,
                                    hourly_rate
                                )

                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")

                # Sleep for configured interval
                time.sleep(Config.COST_UPDATE_INTERVAL)

            logger.info("Pod monitoring loop stopped")

        self._monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitoring_thread.start()

    def stop(self):
        """Stop the pod manager and cleanup"""
        logger.info("Stopping PodManager")
        self._stop_monitoring = True

        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
