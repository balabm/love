import { useState, useEffect } from "react";
import api, { API } from '../api';

export default function SwarmPanel() {
  const [swarm, setSwarm] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    api.get(API.evolution.swarm)
      .then(r => { if (mounted) setSwarm(r.data); })
      .catch(() => { if (mounted) setSwarm({ agents: [], status: "offline" }); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  if (loading) return <div className="p-6 text-gray-400">Loading swarm data...</div>;
  if (!swarm || !swarm.agents?.length) {
    return (
      <div className="p-6">
        <h2 className="text-lg font-semibold mb-2">Swarm Intelligence</h2>
        <p className="text-gray-400">No swarm agents active. The swarm will form as modules come online.</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold mb-4">Swarm Intelligence</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {swarm.agents.map((agent, i) => (
          <div key={i} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2 h-2 rounded-full" style={{ background: agent.active ? '#4ade80' : '#6b7280' }} />
              <span className="font-medium">{agent.name || `Agent ${i + 1}`}</span>
            </div>
            <div className="text-sm text-gray-400">{agent.role || 'swarm node'}</div>
            {agent.load !== undefined && (
              <div className="mt-2 text-xs text-gray-500">Load: {Math.round(agent.load * 100)}%</div>
            )}
          </div>
        ))}
      </div>
      {swarm.coordinator && (
        <div className="mt-4 p-3 bg-gray-800/50 rounded border border-gray-700">
          <div className="text-sm font-medium">Coordinator</div>
          <div className="text-xs text-gray-400">{swarm.coordinator}</div>
        </div>
      )}
    </div>
  );
}
