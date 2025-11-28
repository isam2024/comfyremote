"""
Pod data models for RunPod ComfyUI WebUI
"""
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, List, Dict
from constants import POD_STATUS_INITIALIZING


@dataclass
class PodConfig:
    """Configuration for a ComfyUI pod"""
    public_ip: bool = False
    interruptible: bool = True
    container_disk_gb: int = 70
    volume_disk_gb: int = 50
    models: List[str] = field(default_factory=list)
    custom_nodes: List[str] = field(default_factory=list)
    port: int = 8188

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'PodConfig':
        """Create from dictionary"""
        return cls(
            public_ip=data.get('public_ip', False),
            interruptible=data.get('interruptible', True),
            container_disk_gb=data.get('container_disk_gb', 70),
            volume_disk_gb=data.get('volume_disk_gb', 50),
            models=data.get('models', []),
            custom_nodes=data.get('custom_nodes', []),
            port=data.get('port', 8188),
        )


@dataclass
class Pod:
    """Represents a ComfyUI pod instance"""
    pod_id: str
    name: str
    gpu_id: str
    config: PodConfig
    status: str = POD_STATUS_INITIALIZING
    start_time: Optional[datetime] = None
    endpoint_url: Optional[str] = None
    cost_so_far: float = 0.0
    hourly_rate: float = 0.0
    setup_progress: float = 0.0
    last_heartbeat: Optional[datetime] = None
    setup_logs: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    def __post_init__(self):
        """Initialize timestamp if not provided"""
        if self.start_time is None:
            self.start_time = datetime.now()
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'pod_id': self.pod_id,
            'name': self.name,
            'gpu_id': self.gpu_id,
            'status': self.status,
            'config': self.config.to_dict(),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'endpoint_url': self.endpoint_url,
            'hourly_rate': round(self.hourly_rate, 2),
            'cost_so_far': round(self.cost_so_far, 2),
            'setup_progress': round(self.setup_progress, 1),
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'setup_logs': self.setup_logs[-50:],  # Last 50 log lines
            'error_message': self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Pod':
        """Create from dictionary"""
        config_data = data.get('config', {})
        config = PodConfig.from_dict(config_data) if isinstance(config_data, dict) else config_data

        return cls(
            pod_id=data['pod_id'],
            name=data['name'],
            gpu_id=data['gpu_id'],
            config=config,
            status=data.get('status', POD_STATUS_INITIALIZING),
            start_time=datetime.fromisoformat(data['start_time']) if data.get('start_time') else None,
            endpoint_url=data.get('endpoint_url'),
            cost_so_far=data.get('cost_so_far', 0.0),
            hourly_rate=data.get('hourly_rate', 0.0),
            setup_progress=data.get('setup_progress', 0.0),
            last_heartbeat=datetime.fromisoformat(data['last_heartbeat']) if data.get('last_heartbeat') else None,
            setup_logs=data.get('setup_logs', []),
            error_message=data.get('error_message'),
        )

    def update_heartbeat(self):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = datetime.now()

    def add_log(self, message: str):
        """Add setup log message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.setup_logs.append(f"[{timestamp}] {message}")
        # Keep only last 100 logs
        if len(self.setup_logs) > 100:
            self.setup_logs = self.setup_logs[-100:]

    def get_uptime_seconds(self) -> float:
        """Get pod uptime in seconds"""
        if not self.start_time:
            return 0.0
        # Use utcnow() since start_time is in UTC from RunPod
        return (datetime.utcnow() - self.start_time).total_seconds()

    def get_uptime_formatted(self) -> str:
        """Get formatted uptime string"""
        seconds = int(self.get_uptime_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
