/**
 * API client for RunPod ComfyUI WebUI backend
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api';

/**
 * Generic API request helper
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const config = { ...defaultOptions, ...options };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API request failed: ${endpoint}`, error);
    throw error;
  }
}

/**
 * Pod API endpoints
 */
export const podApi = {
  /**
   * List all pods
   */
  async list() {
    return apiRequest('/pods');
  },

  /**
   * Get pod details
   */
  async get(podId) {
    return apiRequest(`/pods/${podId}`);
  },

  /**
   * Create a new pod
   */
  async create(podData) {
    return apiRequest('/pods', {
      method: 'POST',
      body: JSON.stringify(podData),
    });
  },

  /**
   * Terminate a pod
   */
  async terminate(podId) {
    return apiRequest(`/pods/${podId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Resume a stopped pod
   */
  async resume(podId) {
    return apiRequest(`/pods/${podId}/resume`, {
      method: 'POST',
    });
  },

  /**
   * Get pod logs
   */
  async getLogs(podId) {
    return apiRequest(`/pods/${podId}/logs`);
  },
};

/**
 * GPU API endpoints
 */
export const gpuApi = {
  /**
   * List available GPUs
   */
  async list() {
    return apiRequest('/gpus');
  },

  /**
   * Check GPU availability
   */
  async checkAvailability(gpuId, interruptible = true) {
    return apiRequest('/gpus/check-availability', {
      method: 'POST',
      body: JSON.stringify({
        gpu_id: gpuId,
        interruptible,
      }),
    });
  },
};

/**
 * Monitoring API endpoints
 */
export const monitoringApi = {
  /**
   * Get cost summary
   */
  async getCostSummary() {
    return apiRequest('/monitoring/cost/summary');
  },

  /**
   * Get pod cost
   */
  async getPodCost(podId) {
    return apiRequest(`/monitoring/cost/pod/${podId}`);
  },

  /**
   * Estimate cost
   */
  async estimateCost(gpuId, hours, interruptible = true) {
    return apiRequest('/monitoring/estimate', {
      method: 'POST',
      body: JSON.stringify({
        gpu_id: gpuId,
        hours,
        interruptible,
      }),
    });
  },
};

/**
 * Health API endpoints
 */
export const healthApi = {
  /**
   * Get health status
   */
  async check() {
    return apiRequest('/health');
  },
};

/**
 * Export all APIs
 */
export default {
  pods: podApi,
  gpus: gpuApi,
  monitoring: monitoringApi,
  health: healthApi,
};
