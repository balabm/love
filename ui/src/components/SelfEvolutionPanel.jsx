import { useState, useEffect } from "react";
import api, { API } from '../api';

export default function SelfEvolutionPanel() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    api.get(API.evolution.metrics)
      .then(r => { if (mounted) setMetrics(r.data); })
      .catch(() => { if (mounted) setMetrics({}); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  if (loading) return <div className="p-6 text-gray-400">Loading evolution metrics...</div>;

  const experiments = metrics?.experiments || [];
  const deployments = metrics?.deployments || [];

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold mb-4">Self-Evolution Matrix</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <MetricCard label="Experiments" value={experiments.length} color="#60a5fa" />
        <MetricCard label="Deployments" value={deployments.length} color="#4ade80" />
        <MetricCard label="Mutations" value={metrics?.mutations || 0} color="#f472b6" />
        <MetricCard label="Gaps" value={metrics?.gaps?.length || 0} color="#fbbf24" />
      </div>
      {experiments.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Active Experiments</h3>
          <div className="space-y-2">
            {experiments.slice(0, 10).map((ex, i) => (
              <div key={i} className="flex items-center justify-between bg-gray-800/50 rounded p-2 text-sm">
                <span>{ex.name || `Experiment ${i + 1}`}</span>
                <span className={`px-2 py-0.5 rounded text-xs ${ex.status === 'active' ? 'bg-blue-900/50 text-blue-400' : 'bg-gray-700 text-gray-400'}`}>
                  {ex.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
      {deployments.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Recent Deployments</h3>
          <div className="space-y-2">
            {deployments.slice(0, 10).map((d, i) => (
              <div key={i} className="flex items-center justify-between bg-gray-800/50 rounded p-2 text-sm">
                <span>{d.name || `Deployment ${i + 1}`}</span>
                <span className="text-xs text-gray-500">{d.ts?.slice(0, 16) || ''}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, color }) {
  return (
    <div className="bg-gray-800 rounded-lg p-3 border border-gray-700 text-center">
      <div className="text-2xl font-bold" style={{ color }}>{value}</div>
      <div className="text-xs text-gray-400">{label}</div>
    </div>
  );
}
