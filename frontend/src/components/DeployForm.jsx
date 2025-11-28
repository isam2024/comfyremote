/**
 * Pod deployment form component
 */
import { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import api from '../services/api';

export default function DeployForm({ onClose }) {
  const { state, actions } = useApp();
  const [formData, setFormData] = useState({
    name: '',
    gpu_id: '',
    config: {
      public_ip: false,
      interruptible: true,
      container_disk_gb: 70,
      volume_disk_gb: 50,
      port: 8188,
      models: [],
      custom_nodes: [],
    },
  });
  const [estimatedCost, setEstimatedCost] = useState(null);
  const [deploying, setDeploying] = useState(false);
  const [error, setError] = useState(null);

  // Update cost estimate when GPU or interruptible changes
  useEffect(() => {
    if (formData.gpu_id) {
      const fetchEstimate = async () => {
        try {
          const response = await api.monitoring.estimateCost(
            formData.gpu_id,
            24,
            formData.config.interruptible
          );
          setEstimatedCost(response);
        } catch (err) {
          console.error('Failed to estimate cost:', err);
        }
      };
      fetchEstimate();
    }
  }, [formData.gpu_id, formData.config.interruptible]);

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleConfigChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      config: {
        ...prev.config,
        [field]: value,
      },
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setDeploying(true);

    try {
      const response = await api.pods.create(formData);
      actions.addPod(response);
      onClose();
    } catch (err) {
      console.error('Failed to create pod:', err);
      setError(err.message);
    } finally {
      setDeploying(false);
    }
  };

  const isValid = formData.name && formData.gpu_id;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-dark-600">
          <h2 className="text-2xl font-bold text-white">Deploy New Pod</h2>
          <p className="text-sm text-gray-400 mt-1">
            Configure and deploy a ComfyUI instance
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="bg-red-900/20 border border-red-500 text-red-200 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Pod Name */}
          <div>
            <label className="label">Pod Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              placeholder="e.g., comfyui-production"
              className="input"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              3-50 characters, alphanumeric with hyphens and underscores
            </p>
          </div>

          {/* GPU Selection */}
          <div>
            <label className="label">GPU Type *</label>
            <select
              value={formData.gpu_id}
              onChange={(e) => handleChange('gpu_id', e.target.value)}
              className="select"
              required
            >
              <option value="">Select GPU...</option>
              {state.gpus.map(gpu => (
                <option key={gpu.id} value={gpu.id}>
                  {gpu.display_name} - {gpu.vram_gb}GB VRAM - ${gpu.cost_per_hour}/hr
                </option>
              ))}
            </select>
          </div>

          {/* Cloud Type */}
          <div>
            <label className="label">Cloud Type</label>
            <div className="space-y-2">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  checked={formData.config.interruptible}
                  onChange={() => handleConfigChange('interruptible', true)}
                  className="text-blue-500"
                />
                <span className="text-gray-300">
                  Community Cloud (Interruptible) - Cheaper
                </span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  checked={!formData.config.interruptible}
                  onChange={() => handleConfigChange('interruptible', false)}
                  className="text-blue-500"
                />
                <span className="text-gray-300">
                  Secure Cloud (On-Demand) - 2x price, guaranteed
                </span>
              </label>
            </div>
          </div>

          {/* Public IP */}
          <div>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.config.public_ip}
                onChange={(e) => handleConfigChange('public_ip', e.target.checked)}
                className="text-blue-500"
              />
              <span className="text-gray-300">
                Use Public IP (direct connection, faster)
              </span>
            </label>
          </div>

          {/* Storage */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Container Disk (GB)</label>
              <input
                type="number"
                value={formData.config.container_disk_gb}
                onChange={(e) => handleConfigChange('container_disk_gb', parseInt(e.target.value))}
                min="50"
                max="500"
                className="input"
              />
            </div>
            <div>
              <label className="label">Volume Disk (GB)</label>
              <input
                type="number"
                value={formData.config.volume_disk_gb}
                onChange={(e) => handleConfigChange('volume_disk_gb', parseInt(e.target.value))}
                min="1"
                max="1000"
                className="input"
              />
            </div>
          </div>

          {/* Cost Estimate */}
          {estimatedCost && (
            <div className="bg-blue-900/20 border border-blue-500 rounded-lg p-4">
              <div className="text-sm font-semibold text-blue-300 mb-2">
                Cost Estimate
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-gray-400">Hourly</div>
                  <div className="text-white font-semibold">
                    ${estimatedCost.hourly_rate}/hr
                  </div>
                </div>
                <div>
                  <div className="text-gray-400">24 Hours</div>
                  <div className="text-white font-semibold">
                    ${(estimatedCost.hourly_rate * 24).toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-gray-400">7 Days</div>
                  <div className="text-white font-semibold">
                    ${(estimatedCost.hourly_rate * 24 * 7).toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary flex-1"
              disabled={deploying}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary flex-1"
              disabled={!isValid || deploying}
            >
              {deploying ? 'Deploying...' : 'Deploy Pod'}
            </button>
          </div>

          {isValid && (
            <p className="text-xs text-gray-500 text-center">
              Setup will take approximately 10-15 minutes
            </p>
          )}
        </form>
      </div>
    </div>
  );
}
