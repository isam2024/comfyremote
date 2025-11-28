/**
 * Cost tracking component
 * Displays cost breakdown and analytics
 */
export default function CostTracker({ pods }) {
  if (!pods || pods.length === 0) {
    return null;
  }

  // Calculate totals
  const totalCost = pods.reduce((sum, pod) => sum + (pod.cost_so_far || 0), 0);
  const avgCost = totalCost / pods.length;

  // Group by GPU
  const byGpu = pods.reduce((acc, pod) => {
    const gpu = pod.gpu_id;
    if (!acc[gpu]) {
      acc[gpu] = {
        count: 0,
        cost: 0,
      };
    }
    acc[gpu].count += 1;
    acc[gpu].cost += pod.cost_so_far || 0;
    return acc;
  }, {});

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-white mb-4">
        Cost Breakdown
      </h3>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div>
          <div className="text-sm text-gray-400">Total Cost</div>
          <div className="text-2xl font-bold text-green-400">
            ${totalCost.toFixed(2)}
          </div>
        </div>
        <div>
          <div className="text-sm text-gray-400">Average per Pod</div>
          <div className="text-2xl font-bold text-blue-400">
            ${avgCost.toFixed(2)}
          </div>
        </div>
        <div>
          <div className="text-sm text-gray-400">Active Pods</div>
          <div className="text-2xl font-bold text-white">
            {pods.length}
          </div>
        </div>
      </div>

      {/* By GPU */}
      <div>
        <div className="text-sm font-semibold text-gray-300 mb-2">
          Cost by GPU Type
        </div>
        <div className="space-y-2">
          {Object.entries(byGpu).map(([gpu, data]) => (
            <div key={gpu} className="flex justify-between items-center">
              <div className="text-sm text-gray-400">
                {gpu} <span className="text-gray-500">({data.count})</span>
              </div>
              <div className="text-sm font-semibold text-green-400">
                ${data.cost.toFixed(2)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
