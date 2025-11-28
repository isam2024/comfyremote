# Quick Start Guide

Get your RunPod ComfyUI WebUI up and running in 5 minutes!

## Prerequisites

- Python 3.10+ installed
- Node.js 18+ and npm installed
- RunPod API key ([get one here](https://www.runpod.io/console/user/settings))

## Installation

### Step 1: Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.template .env

# Edit .env and add your RUNPOD_API_KEY
# You can use nano, vim, or any text editor:
nano .env
# Set: RUNPOD_API_KEY=your-actual-api-key-here
```

### Step 2: Setup Frontend

```bash
# Open a new terminal
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

## Running the Application

You'll need two terminal windows open:

### Terminal 1 - Backend Server

```bash
cd backend
source venv/bin/activate  # Activate venv if not already active
python server.py
```

You should see:
```
Starting RunPod ComfyUI WebUI on 0.0.0.0:5000
Debug mode: True
```

### Terminal 2 - Frontend Dev Server

```bash
cd frontend
npm run dev
```

You should see:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

## First Deployment

1. **Open your browser** to http://localhost:5173

2. **Click "Deploy New Pod"**

3. **Configure your pod:**
   - **Name**: `my-first-comfyui` (or any name you like)
   - **GPU**: Start with `NVIDIA GeForce RTX 3070` (budget-friendly for testing)
   - **Cloud Type**: Community Cloud (Interruptible) - cheaper
   - **Public IP**: Leave unchecked (proxy is fine for testing)
   - **Storage**: Leave defaults (70GB container, 50GB volume)

4. **Check cost estimate:**
   - You'll see hourly, daily, and weekly cost projections
   - RTX 3070 is ~$0.07/hour (~$1.68/day)

5. **Click "Deploy Pod"**

6. **Watch the progress:**
   - Status will show "initializing"
   - Progress bar will update as setup proceeds
   - Click "Logs" to see detailed progress
   - Setup takes 10-15 minutes

7. **Once running:**
   - Status changes to "running"
   - "Open ComfyUI" button appears
   - Click it to access your ComfyUI instance!

8. **When done:**
   - Click "Terminate" to stop the pod
   - This stops billing immediately

## Troubleshooting

### Backend won't start

**Error: "RUNPOD_API_KEY not found"**
- Make sure `.env` file exists in `backend/` directory
- Verify RUNPOD_API_KEY is set correctly (no quotes needed in .env)
- Restart the backend server after changing .env

**Error: "GPU specs file not found"**
- Verify `data/gpu_specs.json` exists
- Run from project root or ensure paths are correct

### Frontend won't start

**Error: "Cannot find module"**
- Make sure you ran `npm install` in frontend directory
- Try deleting `node_modules` and running `npm install` again

**Can't connect to backend**
- Verify backend is running on port 5000
- Check browser console for errors
- Try accessing http://localhost:5000/api/health directly

### Pod deployment issues

**Pod stuck at "initializing"**
- This is normal - setup takes 10-15 minutes
- Click "Logs" to see progress
- Models are downloading (FLUX models are large)

**Deployment failed**
- Check if you have sufficient RunPod credits
- Verify the selected GPU is available (try a different GPU)
- Check backend logs for detailed error messages

## Next Steps

### Explore the Dashboard
- View all your pods in the grid
- Monitor real-time costs
- See setup progress and logs

### Try Different GPUs
- RTX 4090 for faster generation (~$0.20/hr)
- A100 for production workloads (~$1.19/hr)
- Compare performance vs cost

### Cost Management
- Monitor total costs in the header
- View per-pod costs in pod cards
- Check cost breakdown section
- Remember to terminate pods when not in use!

### Advanced Features (Coming in Phase 2)
- Upload and execute ComfyUI workflows
- Save deployment configurations as templates
- Manage multiple pods simultaneously
- Advanced monitoring with GPU metrics

## Development Mode

### Backend Development
```bash
cd backend
source venv/bin/activate

# Run with auto-reload
export FLASK_DEBUG=True
python server.py
```

### Frontend Development
```bash
cd frontend

# Vite dev server has HMR (Hot Module Replacement)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Running Tests
```bash
cd backend
pytest tests/
```

## Configuration Options

### Environment Variables

Edit `backend/.env`:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key
DEBUG=True
HOST=0.0.0.0
PORT=5000

# RunPod API
RUNPOD_API_KEY=your-key-here
RUNPOD_API_TIMEOUT=800

# ComfyUI
COMFYUI_PORT=8188
COMFYUI_IMAGE=runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# Cost Tracking
COST_UPDATE_INTERVAL=60  # seconds
```

## Tips & Best Practices

1. **Start Small**: Begin with budget GPUs (RTX 3070/4090) for testing
2. **Monitor Costs**: Check the dashboard frequently, costs accumulate while running
3. **Terminate When Done**: Always terminate pods to stop billing
4. **Use Community Cloud**: Interruptible instances are 50% cheaper
5. **Save Configurations**: Note which settings work best for your use case
6. **Check Logs**: If something goes wrong, logs usually have the answer

## Getting Help

- **Documentation**: See [README.md](./README.md) for full documentation
- **API Reference**: Check [docs/API.md](./docs/API.md) for API details
- **Issues**: Report bugs or request features on GitHub
- **RunPod Support**: Visit [RunPod Discord](https://discord.gg/runpod)

## What's Next?

Now that you have the MVP running:
- Deploy your first pod
- Experiment with different GPUs
- Monitor costs and performance
- Wait for Phase 2 features (workflow management, templates, etc.)

---

**Enjoy deploying ComfyUI on RunPod! 🚀**
