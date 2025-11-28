/**
 * Main application component
 */
import { useEffect, useCallback } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { useSSE } from './hooks/useSSE';
import api from './services/api';
import Dashboard from './components/Dashboard';

function AppContent() {
  const { state, actions } = useApp();

  // Handle SSE messages
  const handleSSEMessage = useCallback((message) => {
    console.log('SSE message:', message);

    switch (message.type) {
      case 'pod_status':
        // Update pod status
        actions.updatePod(message.data.pod_id, {
          status: message.data.status,
          endpoint_url: message.data.endpoint_url,
          uptime: message.data.uptime,
        });
        break;

      case 'setup_progress':
        // Update setup progress
        actions.updatePod(message.data.pod_id, {
          setup_progress: message.data.percent,
          setup_logs: message.data.logs,
        });
        break;

      case 'cost_update':
        // Update pod cost
        actions.updatePod(message.data.pod_id, {
          cost_so_far: message.data.cost_so_far,
        });
        break;

      case 'pod_created':
        // Fetch new pod details
        loadPods();
        break;

      case 'pod_terminated':
        // Mark pod as terminated
        actions.updatePod(message.data.pod_id, {
          status: 'terminated',
        });
        break;

      case 'error':
        console.error('SSE error:', message.data);
        actions.setError(message.data.message);
        break;

      default:
        console.log('Unknown SSE event type:', message.type);
    }
  }, [actions]);

  // Connect to SSE
  const { connected, error: sseError } = useSSE(handleSSEMessage);

  // Load initial data
  const loadPods = useCallback(async () => {
    try {
      const response = await api.pods.list();
      actions.setPods(response.pods);
      actions.setCostSummary({
        total_cost: response.total_cost,
        total_pods: response.count,
      });
    } catch (error) {
      console.error('Failed to load pods:', error);
      actions.setError(error.message);
    }
  }, [actions]);

  const loadGPUs = useCallback(async () => {
    try {
      const response = await api.gpus.list();
      actions.setGpus(response.gpus);
    } catch (error) {
      console.error('Failed to load GPUs:', error);
    }
  }, [actions]);

  // Load data on mount
  useEffect(() => {
    loadPods();
    loadGPUs();
  }, [loadPods, loadGPUs]);

  // Refresh pods periodically (fallback if SSE fails)
  useEffect(() => {
    if (!connected) {
      const interval = setInterval(loadPods, 30000); // Every 30s
      return () => clearInterval(interval);
    }
  }, [connected, loadPods]);

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <header className="bg-dark-800 border-b border-dark-600 py-4 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">
              RunPod ComfyUI WebUI
            </h1>
            <p className="text-sm text-gray-400 mt-1">
              Deploy and manage ComfyUI instances
            </p>
          </div>

          <div className="flex items-center space-x-4">
            {/* Connection status */}
            <div className="flex items-center space-x-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  connected ? 'bg-green-500' : 'bg-red-500 animate-pulse'
                }`}
              />
              <span className="text-sm text-gray-400">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            {/* Cost summary */}
            <div className="text-right">
              <div className="text-sm text-gray-400">Total Cost</div>
              <div className="text-xl font-bold text-green-400">
                ${state.costSummary.total_cost.toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto py-6 px-6">
        {state.error && (
          <div className="bg-red-900/20 border border-red-500 text-red-200 px-4 py-3 rounded-lg mb-6">
            <strong>Error:</strong> {state.error}
          </div>
        )}

        <Dashboard />
      </main>
    </div>
  );
}

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;
