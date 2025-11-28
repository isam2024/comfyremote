/**
 * Pod card component
 * Displays individual pod information
 */
import { useState } from 'react';
import api from '../services/api';
import { useApp } from '../context/AppContext';

export default function PodCard({ pod }) {
  const { actions } = useApp();
  const [terminating, setTerminating] = useState(false);
  const [showLogs, setShowLogs] = useState(false);

  const handleTerminate = async () => {
    if (!confirm(`Are you sure you want to terminate pod "${pod.name}"?`)) {
      return;
    }

    setTerminating(true);

    try {
      await api.pods.terminate(pod.pod_id);
      // State will be updated via SSE
    } catch (error) {
      console.error('Failed to terminate pod:', error);
      alert(`Failed to terminate pod: ${error.message}`);
    } finally {
      setTerminating(false);
    }
  };

  const handleOpenComfyUI = () => {
    if (pod.endpoint_url) {
      window.open(pod.endpoint_url, '_blank');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'initializing':
        return 'text-yellow-400';
      case 'running':
        return 'text-green-400';
      case 'failed':
        return 'text-red-400';
      case 'stopped':
      case 'terminated':
        return 'text-gray-400';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusDot = (status) => {
    switch (status) {
      case 'initializing':
        return 'status-initializing';
      case 'running':
        return 'status-running';
      case 'failed':
        return 'status-failed';
      case 'stopped':
        return 'status-stopped';
      case 'terminated':
        return 'status-terminated';
      default:
        return 'status-stopped';
    }
  };

  return (
    <div className="card card-hover">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">{pod.name}</h3>
          <p className="text-sm text-gray-400">{pod.pod_id}</p>
        </div>
        <div className={`text-sm font-medium ${getStatusColor(pod.status)}`}>
          <span className={`status-dot ${getStatusDot(pod.status)}`} />
          {pod.status}
        </div>
      </div>

      {/* GPU Info */}
      <div className="space-y-2 mb-4">
        <div className="text-sm text-gray-400">
          GPU: <span className="text-white">{pod.gpu_id}</span>
        </div>
        {pod.status === 'initializing' && (
          <div>
            <div className="text-sm text-gray-400 mb-1">
              Setup Progress: {pod.setup_progress}%
            </div>
            <div className="w-full bg-dark-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${pod.setup_progress}%` }}
              />
            </div>
          </div>
        )}
        {pod.status === 'running' && pod.endpoint_url && (
          <div className="text-sm text-gray-400">
            Endpoint: <span className="text-blue-400 truncate">{pod.endpoint_url}</span>
          </div>
        )}
      </div>

      {/* Cost */}
      <div className="mb-4">
        <div className="text-sm text-gray-400">
          Cost: <span className="text-green-400 font-semibold">${pod.cost_so_far.toFixed(2)}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex space-x-2">
        {pod.status === 'running' && pod.endpoint_url && (
          <button
            onClick={handleOpenComfyUI}
            className="btn btn-primary flex-1"
          >
            Open ComfyUI
          </button>
        )}

        {(pod.status === 'running' || pod.status === 'initializing') && (
          <button
            onClick={handleTerminate}
            disabled={terminating}
            className="btn btn-danger flex-1"
          >
            {terminating ? 'Terminating...' : 'Terminate'}
          </button>
        )}

        {(pod.status === 'initializing' || pod.setup_logs?.length > 0) && (
          <button
            onClick={() => setShowLogs(!showLogs)}
            className="btn btn-secondary"
          >
            {showLogs ? 'Hide' : 'Logs'}
          </button>
        )}
      </div>

      {/* Logs */}
      {showLogs && pod.setup_logs && (
        <div className="mt-4 bg-dark-900 rounded p-3 max-h-48 overflow-y-auto">
          <div className="text-xs font-mono text-gray-400">
            {pod.setup_logs.map((log, i) => (
              <div key={i}>{log}</div>
            ))}
          </div>
        </div>
      )}

      {/* Error message */}
      {pod.error_message && (
        <div className="mt-4 bg-red-900/20 border border-red-500 text-red-200 text-sm px-3 py-2 rounded">
          {pod.error_message}
        </div>
      )}
    </div>
  );
}
