# RunPod ComfyUI WebUI

A production-ready web application for deploying and managing ComfyUI instances on RunPod infrastructure with real-time monitoring, cost tracking, and workflow management.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![React](https://img.shields.io/badge/react-18+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

### MVP (Phase 1) ✓
- **Pod Deployment**: Deploy ComfyUI instances with GPU selection
- **Real-time Dashboard**: Live status updates via Server-Sent Events (SSE)
- **Cost Tracking**: Real-time cost calculation and projections
- **Pod Lifecycle Management**: Create, monitor, and terminate pods
- **GPU Selection**: Choose from 30+ GPU types across all tiers

### Coming Soon (Phase 2-3)
- **Workflow Management**: Upload and execute ComfyUI workflows
- **Configuration Templates**: Save and reuse deployment configs
- **Multi-Pod Operations**: Bulk deployment and management
- **Advanced Monitoring**: GPU utilization, memory tracking
- **Authentication**: JWT-based user authentication
- **Cost Analytics**: Daily/weekly/monthly reports with alerts

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Browser                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         React Application (Vite)                        │ │
│  │  Dashboard | Pod Manager | Cost Tracker | Monitoring   │ │
│  └────────────────────────────────────────────────────────┘ │
│         │ REST API              │ SSE Stream                 │
└─────────┼───────────────────────┼────────────────────────────┘
          │                       │
┌─────────▼───────────────────────▼────────────────────────────┐
│                  Flask Backend                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Routes: Pods | SSE | Monitoring | Health | Workflows  │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Services: PodManager | CostCalculator | SSEBroadcaster│ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────┬───────────────────────────────────┘
                            │
                ┌───────────▼──────────┐
                │    RunPod API        │
                └──────────────────────┘
```

## Tech Stack

### Backend
- **Framework**: Flask 3.0 with Blueprint architecture
- **Real-time**: Server-Sent Events (SSE)
- **Language**: Python 3.10+
- **API Client**: RunPod REST API

### Frontend
- **Framework**: React 18+ with Hooks
- **State Management**: Context API + useReducer
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **Real-time**: EventSource API (SSE)

## Quick Start

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ and npm
- RunPod API key ([get one here](https://www.runpod.io/console/user/settings))

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd project
```

2. **Setup Backend**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.template .env
# Edit .env and add your RUNPOD_API_KEY
```

3. **Setup Frontend**
```bash
cd ../frontend

# Install dependencies
npm install
```

### Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python server.py
```
Backend will start on http://localhost:5000

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```
Frontend will start on http://localhost:5173

### First Deployment

1. Open http://localhost:5173 in your browser
2. Click "Deploy New Pod"
3. Select a GPU (start with RTX 3070 for testing)
4. Configure settings:
   - Name: `my-first-comfyui`
   - Public IP: Optional
   - Interruptible: Yes (cheaper)
5. Click "Deploy"
6. Watch real-time setup progress (10-15 minutes)
7. Access ComfyUI via the endpoint URL once running

## API Documentation

### Core Endpoints

#### Pods
```
GET    /api/pods              # List all pods
POST   /api/pods              # Create new pod
GET    /api/pods/:id          # Get pod details
DELETE /api/pods/:id          # Terminate pod
GET    /api/pods/:id/logs     # Get setup logs
```

#### Monitoring
```
GET    /api/monitoring/cost/summary      # Cost summary
GET    /api/monitoring/cost/pod/:id      # Pod cost breakdown
POST   /api/monitoring/estimate          # Estimate cost
```

#### Configuration
```
GET    /api/gpus              # List available GPUs
GET    /api/health            # System health check
```

#### Real-time
```
GET    /api/stream/events     # SSE event stream
```

### SSE Event Types
```javascript
{type: 'connected', data: {...}}         // Initial connection
{type: 'pod_status', data: {...}}        // Pod status update
{type: 'setup_progress', data: {...}}    // Setup progress
{type: 'cost_update', data: {...}}       // Cost update
{type: 'pod_created', data: {...}}       // New pod created
{type: 'pod_terminated', data: {...}}    // Pod terminated
{type: 'error', data: {...}}             // Error occurred
```

## Project Structure

```
project/
├── backend/                   # Flask backend
│   ├── routes/               # API blueprints
│   ├── services/             # Core business logic
│   ├── models/               # Data models
│   ├── utils/                # Utilities
│   ├── server.py             # Flask app entry point
│   ├── config.py             # Configuration
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   ├── context/          # State management
│   │   └── services/         # API client
│   ├── package.json          # Node dependencies
│   └── vite.config.js        # Vite configuration
├── data/
│   └── gpu_specs.json        # GPU database
├── docs/                     # Documentation
├── tests/                    # Test suite
├── .env.template             # Environment template
└── README.md                 # This file
```

## GPU Options

The system supports 30+ GPU types across 4 tiers:

### Budget Tier ($0.06-0.19/hr)
- RTX 3070, 3080, 3090
- RTX A2000-A5000
- Tesla V100

### Mid Tier ($0.20-0.68/hr)
- RTX 4080, 4090, 5080, 5090
- RTX A6000
- L40, L40S

### High Tier ($0.95-1.50/hr)
- A100 80GB
- H100 (80GB, NVL, PCIe)

### Premium Tier ($2.99-8.64/hr)
- H200
- B200
- AMD MI300X

## Cost Management

### Pricing Model
- **Community Cloud** (Interruptible): Base pricing
- **Secure Cloud** (On-Demand): 2x base pricing

### Example Costs (Community Cloud)
- RTX 3070: $0.07/hr (~$1.68/day)
- RTX 4090: $0.20/hr (~$4.80/day)
- A100 80GB: $1.19/hr (~$28.56/day)
- H100: $1.50/hr (~$36.00/day)

### Cost Optimization Tips
1. Use interruptible (Community Cloud) for development
2. Start with budget GPUs for testing
3. Terminate pods when not in use
4. Monitor real-time costs in dashboard

## Development

### Running Tests
```bash
cd backend
pytest tests/
```

### Code Style
```bash
# Format code
black backend/

# Lint
flake8 backend/
```

### Building for Production
```bash
# Build frontend
cd frontend
npm run build

# Deploy backend with Gunicorn
cd backend
gunicorn -w 4 -k gevent server:app
```

## Troubleshooting

### Backend Issues

**"RUNPOD_API_KEY not found"**
- Ensure `.env` file exists in backend directory
- Verify RUNPOD_API_KEY is set correctly

**"GPU specs file not found"**
- Check that `data/gpu_specs.json` exists
- Verify file path in `config.py`

### Frontend Issues

**"Cannot connect to backend"**
- Ensure backend is running on port 5000
- Check CORS configuration in `server.py`

**SSE connection drops**
- Normal behavior, auto-reconnects
- Check browser console for errors

### Pod Deployment Issues

**Pod stuck in "initializing"**
- Check pod logs via API or dashboard
- Verify RunPod has capacity for selected GPU
- Increase timeout in `constants.py`

**Pod failed to start**
- Check RunPod API status
- Verify sufficient quota/credits
- Review error message in pod details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [docs/](./docs/)
- **RunPod Support**: [RunPod Discord](https://discord.gg/runpod)

## Roadmap

### Phase 1 (MVP) ✓
- [x] Pod deployment
- [x] Real-time monitoring
- [x] Cost tracking
- [x] Basic dashboard

### Phase 2 (Weeks 3-4)
- [ ] Workflow management
- [ ] Configuration templates
- [ ] Multi-pod operations
- [ ] Advanced monitoring

### Phase 3 (Weeks 5-6)
- [ ] Authentication
- [ ] Cost analytics
- [ ] Model management
- [ ] Alerts & notifications

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Frontend powered by [React](https://react.dev/) and [Vite](https://vitejs.dev/)
- Deployed on [RunPod](https://runpod.io/)
- ComfyUI by [comfyanonymous](https://github.com/comfyanonymous/ComfyUI)

---

**Made with ❤️ for the ComfyUI community**
