import { useState, useEffect } from "react";
import api, { API } from '../api';

export default function NotificationDashboard() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    api.get(API.notifications.recent)
      .then(r => { if (mounted) setNotifications(r.data?.notifications || []); })
      .catch(() => { if (mounted) setNotifications([]); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  if (loading) return <div className="p-6 text-gray-400">Loading notifications...</div>;

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold mb-4">Notifications</h2>
      {notifications.length === 0 ? (
        <p className="text-gray-400">No recent notifications.</p>
      ) : (
        <div className="space-y-2">
          {notifications.map((n, i) => (
            <div key={i} className="bg-gray-800 rounded p-3 border border-gray-700 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium">{n.category || "notification"}</span>
                <span className="text-xs text-gray-500">{n.ts?.slice(0, 16) || ""}</span>
              </div>
              <p className="text-gray-300 mt-1">{n.message}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
