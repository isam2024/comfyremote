/**
 * Main dashboard component
 * Displays pods grid and deployment form
 */
import { useState } from 'react';
import { useApp } from '../context/AppContext';
import PodCard from './PodCard';
import DeployForm from './DeployForm';
import CostTracker from './CostTracker';

export default function Dashboard() {
  const { state } = useApp();
  const [showDeployForm, setShowDeployForm] = useState(false);

  const pods = Object.values(state.pods);
  const activePods = pods.filter(p => p.status === 'running' || p.status === 'initializing');
  const terminatedPods = pods.filter(p => p.status === 'terminated' || p.status === 'stopped');

  return (
    <div className="space-y-6">
      {/* Stats overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="text-sm text-gray-400 mb-1">Total Pods</div>
          <div className="text-3xl font-bold text-white">{pods.length}</div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-400 mb-1">Active Pods</div>
          <div className="text-3xl font-bold text-green-400">{activePods.length}</div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-400 mb-1">Total Cost</div>
          <div className="text-3xl font-bold text-blue-400">
            ${state.costSummary.total_cost.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Deploy button */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-white">Pods</h2>
        <button
          onClick={() => setShowDeployForm(true)}
          className="btn btn-primary"
        >
          + Deploy New Pod
        </button>
      </div>

      {/* Deploy form modal */}
      {showDeployForm && (
        <DeployForm onClose={() => setShowDeployForm(false)} />
      )}

      {/* Pods grid */}
      {pods.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-400 text-lg mb-4">
            No pods deployed yet
          </p>
          <button
            onClick={() => setShowDeployForm(true)}
            className="btn btn-primary"
          >
            Deploy Your First Pod
          </button>
        </div>
      ) : (
        <>
          {/* Active pods */}
          {activePods.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-300 mb-3">
                Active ({activePods.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {activePods.map(pod => (
                  <PodCard key={pod.pod_id} pod={pod} />
                ))}
              </div>
            </div>
          )}

          {/* Terminated pods */}
          {terminatedPods.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-300 mb-3">
                Terminated ({terminatedPods.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {terminatedPods.slice(0, 6).map(pod => (
                  <PodCard key={pod.pod_id} pod={pod} />
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Cost tracker */}
      <CostTracker pods={activePods} />
    </div>
  );
}
