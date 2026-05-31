import { useState, useEffect } from "react";
import api, { API } from '../api';

export default function AutonomyPanel() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    api.get(API.evolution.status)
      .then(r => { if (mounted) setStatus(r.data); })
      .catch(() => { if (mounted) setStatus({ systems: [] }); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  if (loading) return <div className="p-6 text-gray-400">Loading autonomy data...</div>;

  const systems = status?.systems || [];
  const ready = systems.filter(s => s.status === 'ready').length;
  const failed = systems.filter(s => s.status === 'failed').length;

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold mb-4">Autonomy Supervisor</h2>
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700 text-center">
          <div className="text-2xl font-bold text-green-400">{ready}</div>
          <div className="text-xs text-gray-400">Ready</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700 text-center">
          <div className="text-2xl font-bold text-yellow-400">{systems.length - ready - failed}</div>
          <div className="text-xs text-gray-400">Other</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700 text-center">
          <div className="text-2xl font-bold text-red-400">{failed}</div>
          <div className="text-xs text-gray-400">Failed</div>
        </div>
      </div>
      <div className="space-y-2">
        {systems.slice(0, 20).map((s, i) => (
          <div key={i} className="flex items-center justify-between bg-gray-800/50 rounded p-2 text-sm">
            <span className="font-medium">{s.name || s.module || `Module ${i + 1}`}</span>
            <span className={`px-2 py-0.5 rounded text-xs ${s.status === 'ready' ? 'bg-green-900/50 text-green-400' : s.status === 'failed' ? 'bg-red-900/50 text-red-400' : 'bg-gray-700 text-gray-400'}`}>
              {s.status}
            </span>
          </div>
        ))}
        {systems.length > 20 && (
          <div className="text-center text-xs text-gray-500">+ {systems.length - 20} more modules</div>
        )}
      </div>
    </div>
  );
}
