"""
Centralized constants for RunPod ComfyUI WebUI
"""

# Pod Status
POD_STATUS_INITIALIZING = 'initializing'
POD_STATUS_RUNNING = 'running'
POD_STATUS_FAILED = 'failed'
POD_STATUS_STOPPED = 'stopped'
POD_STATUS_TERMINATED = 'terminated'

POD_STATUSES = [
    POD_STATUS_INITIALIZING,
    POD_STATUS_RUNNING,
    POD_STATUS_FAILED,
    POD_STATUS_STOPPED,
    POD_STATUS_TERMINATED,
]

# RunPod API Status Mappings
RUNPOD_STATUS_MAP = {
    'PENDING': POD_STATUS_INITIALIZING,
    'RUNNING': POD_STATUS_RUNNING,
    'EXITED': POD_STATUS_STOPPED,  # EXITED = stopped, can be started again
    'FAILED': POD_STATUS_FAILED,
}

# SSE Event Types
SSE_EVENT_CONNECTED = 'connected'
SSE_EVENT_POD_STATUS = 'pod_status'
SSE_EVENT_SETUP_PROGRESS = 'setup_progress'
SSE_EVENT_COST_UPDATE = 'cost_update'
SSE_EVENT_POD_CREATED = 'pod_created'
SSE_EVENT_POD_TERMINATED = 'pod_terminated'
SSE_EVENT_ERROR = 'error'

# Default Models to Install
DEFAULT_MODELS = {
    'diffusion': [
        'jibMixFlux_v8Accentueight.safetensors'
    ],
    'clip': [
        'clip_l.safetensors',
        't5xxl_fp16.safetensors'
    ],
    'vae': [
        'ae.safetensors'
    ],
    'loras': [
        'PlotL9.safetensors',
        'abs.safetensors'
    ]
}

# Default Custom Nodes
DEFAULT_CUSTOM_NODES = [
    'https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git',
    'https://github.com/GizmoR13/PG-Nodes.git',
]

# Model Download URLs
MODEL_URLS = {
    'jibMixFlux_v8Accentueight.safetensors': 'https://huggingface.co/John6666/jib-mix-flux-v8accentueight-nsfw-bf16-flux/resolve/main/jibMixFlux_v8AccentueightNSFW.safetensors',
    'clip_l.safetensors': 'https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors',
    't5xxl_fp16.safetensors': 'https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors',
    'ae.safetensors': 'https://haxed.me.uk/pusher/ae.safetensors',
    'PlotL9.safetensors': 'https://haxed.me.uk/pusher/PlotL9.safetensors',
    'abs.safetensors': 'https://haxed.me.uk/pusher/abs.safetensors',
}

# Setup Progress Steps
SETUP_STEPS = [
    {'step': 'creating_pod', 'description': 'Creating RunPod instance', 'weight': 5},
    {'step': 'installing_dependencies', 'description': 'Installing system dependencies', 'weight': 10},
    {'step': 'cloning_comfyui', 'description': 'Cloning ComfyUI repository', 'weight': 10},
    {'step': 'installing_requirements', 'description': 'Installing Python requirements', 'weight': 15},
    {'step': 'downloading_models', 'description': 'Downloading AI models', 'weight': 50},
    {'step': 'installing_custom_nodes', 'description': 'Installing custom nodes', 'weight': 5},
    {'step': 'starting_comfyui', 'description': 'Starting ComfyUI server', 'weight': 5},
]

# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_ERROR = 500

# API Endpoints
API_PREFIX = '/api'
API_PODS = f'{API_PREFIX}/pods'
API_MONITORING = f'{API_PREFIX}/monitoring'
API_WORKFLOWS = f'{API_PREFIX}/workflows'
API_TEMPLATES = f'{API_PREFIX}/templates'
API_GPUS = f'{API_PREFIX}/gpus'
API_HEALTH = f'{API_PREFIX}/health'
API_SSE = f'{API_PREFIX}/stream/events'

# Timeouts (seconds)
POD_CREATION_TIMEOUT = 900  # 15 minutes
POD_STATUS_POLL_INTERVAL = 10
COMFYUI_STARTUP_TIMEOUT = 300  # 5 minutes
