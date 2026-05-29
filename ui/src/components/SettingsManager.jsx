import { useState, useEffect, useCallback } from "react";
import api from "../api";
import "./SettingsManager.css";

const TABS = [
  { id: "profile", label: "Profile", icon: "👤" },
  { id: "companion", label: "Companion", icon: "💜" },
  { id: "work", label: "Work", icon: "💼" },
  { id: "finance", label: "Finance", icon: "💰" },
  { id: "models", label: "Models", icon: "🧠" },
  { id: "voice", label: "Voice", icon: "🎙️" },
  { id: "evolution", label: "Evolution", icon: "🧬" },
  { id: "privacy", label: "Privacy", icon: "🔒" },
  { id: "devices", label: "Devices", icon: "📱" },
];

export default function SettingsManager() {
  const [activeTab, setActiveTab] = useState("profile");
  const [settings, setSettings] = useState(null);
  const [devices, setDevices] = useState([]);
  const [deviceHealth, setDeviceHealth] = useState([]);
  const [presence, setPresence] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);
  const [newDevice, setNewDevice] = useState({ device_id: "", name: "", role: "companion", capabilities: [], os_type: "" });
  const [editValues, setEditValues] = useState({});

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [s, d, h, p] = await Promise.all([
        api.get("/settings").catch(() => ({ data: null })),
        api.get("/ecosystem/devices").catch(() => ({ data: { devices: [] } })),
        api.get("/ecosystem/devices/health").catch(() => ({ data: { health: [] } })),
        api.get("/ecosystem/presence").catch(() => ({ data: null })),
      ]);
      if (s.data && !s.data.error) setSettings(s.data);
      setDevices(d.data?.devices || []);
      setDeviceHealth(h.data?.health || []);
      setPresence(p.data);
      setError(null);
    } catch (e) {
      setError("Failed to load settings. Is LOVE running?");
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  useEffect(() => {
    if (settings) {
      setEditValues(settings[activeTab] || {});
    }
  }, [activeTab, settings]);

  const saveSection = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await api.put("/settings", { section: activeTab, values: editValues });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      // Refresh
      const s = await api.get("/settings");
      if (s.data && !s.data.error) setSettings(s.data);
    } catch (e) {
      setError("Save failed: " + e.message);
    }
    setSaving(false);
  };

  const registerDevice = async () => {
    if (!newDevice.device_id || !newDevice.name) return;
    try {
      await api.post("/ecosystem/devices/register", newDevice);
      setNewDevice({ device_id: "", name: "", role: "companion", capabilities: [], os_type: "" });
      fetchAll();
    } catch (e) {
      setError("Device registration failed: " + e.message);
    }
  };

  const toggleCapability = (cap) => {
    setNewDevice((prev) => ({
      ...prev,
      capabilities: prev.capabilities.includes(cap)
        ? prev.capabilities.filter((c) => c !== cap)
        : [...prev.capabilities, cap],
    }));
  };

  const updateEdit = (key, value) => {
    setEditValues((prev) => ({ ...prev, [key]: value }));
  };

  if (loading) return <div className="settings-loading">Loading preferences...</div>;
  if (!settings) return <div className="settings-error">{error || "Could not load settings"}</div>;

  const renderField = (key, value, type = "text") => {
    if (typeof value === "boolean") {
      return (
        <label className="settings-toggle" key={key}>
          <input type="checkbox" checked={!!editValues[key]} onChange={(e) => updateEdit(key, e.target.checked)} />
          <span className="toggle-slider" />
          <span className="toggle-label">{key.replace(/_/g, " ")}</span>
        </label>
      );
    }
    if (Array.isArray(value)) {
      return (
        <div className="settings-field" key={key}>
          <label>{key.replace(/_/g, " ")}</label>
          <textarea
            value={(editValues[key] || []).join(", ")}
            onChange={(e) => updateEdit(key, e.target.value.split(",").map((s) => s.trim()).filter(Boolean))}
            rows={2}
          />
          <span className="field-hint">Comma-separated values</span>
        </div>
      );
    }
    if (type === "number") {
      return (
        <div className="settings-field" key={key}>
          <label>{key.replace(/_/g, " ")}</label>
          <input type="number" step="0.1" value={editValues[key] ?? ""} onChange={(e) => updateEdit(key, parseFloat(e.target.value))} />
        </div>
      );
    }
    return (
      <div className="settings-field" key={key}>
        <label>{key.replace(/_/g, " ")}</label>
        <input type="text" value={editValues[key] ?? ""} onChange={(e) => updateEdit(key, e.target.value)} />
      </div>
    );
  };

  const sectionMeta = {
    profile: { title: "User Profile", desc: "Your identity and timezone" },
    companion: { title: "Companion Settings", desc: "AI personality and name" },
    work: { title: "Work Configuration", desc: "Hours, limits, dev folders" },
    finance: { title: "Finance Preferences", desc: "Watchlist, risk, currency" },
    models: { title: "AI Models", desc: "LLM selection and endpoints" },
    voice: { title: "Voice Interface", desc: "Wake word, STT, TTS" },
    evolution: { title: "Self-Evolution", desc: "Auto-heal, optimization" },
    privacy: { title: "Privacy & Data", desc: "Local-only, cloud sync, logs" },
    devices: { title: "Device Ecosystem", desc: "Manage connected devices" },
  };

  const meta = sectionMeta[activeTab];

  return (
    <div className="settings-manager">
      <header className="settings-header">
        <h2>⚙️ Settings &amp; Devices</h2>
        <div className="settings-actions">
          {saved && <span className="settings-saved">✓ Saved</span>}
          {activeTab !== "devices" && (
            <button className="settings-save-btn" onClick={saveSection} disabled={saving}>
              {saving ? "Saving..." : "Save Changes"}
            </button>
          )}
          <button className="settings-refresh-btn" onClick={fetchAll} title="Refresh">
            🔄
          </button>
        </div>
      </header>

      {error && <div className="settings-error-banner">{error}</div>}

      <div className="settings-body">
        <nav className="settings-tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`settings-tab ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => { setActiveTab(tab.id); setError(null); }}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>

        <div className="settings-panel">
          <div className="settings-section-header">
            <h3>{meta.title}</h3>
            <p>{meta.desc}</p>
          </div>

          {activeTab === "devices" ? (
            <div className="devices-panel">
              {/* Presence */}
              {presence && (
                <div className="presence-card">
                  <h4>👤 User Presence</h4>
                  <div className="presence-status">
                    <span className={presence.present ? "present" : "away"}>
                      {presence.present ? "● Present" : "○ Away"}
                    </span>
                    {presence.active_device_name && (
                      <span>Active: {presence.active_device_name}</span>
                    )}
                    {presence.likely_activity && (
                      <span>Activity: {presence.likely_activity}</span>
                    )}
                  </div>
                  {presence.online_devices?.length > 0 && (
                    <div className="online-devices">
                      Online: {presence.online_devices.join(", ")}
                    </div>
                  )}
                </div>
              )}

              {/* Device list */}
              <div className="device-list">
                <h4>📱 Registered Devices ({devices.length})</h4>
                {devices.length === 0 && <p className="settings-empty">No devices registered yet.</p>}
                {devices.map((dev) => {
                  const health = deviceHealth.find((h) => h.device_id === dev.id) || {};
                  return (
                    <div key={dev.id} className={`device-card ${dev.online ? "online" : "offline"}`}>
                      <div className="device-card-header">
                        <span className="device-name">{dev.name || dev.id}</span>
                        <span className={`device-status ${dev.online ? "online" : "offline"}`}>
                          {dev.online ? "● online" : "○ offline"}
                        </span>
                      </div>
                      <div className="device-meta">
                        <span>Role: {dev.role}</span>
                        <span>OS: {dev.os_type || "unknown"}</span>
                        {dev.battery != null && <span>Battery: {dev.battery}%</span>}
                        {dev.ip_address && <span>IP: {dev.ip_address}</span>}
                      </div>
                      {dev.capabilities?.length > 0 && (
                        <div className="device-caps">
                          {dev.capabilities.map((c) => (
                            <span key={c} className="device-cap">{c}</span>
                          ))}
                        </div>
                      )}
                      {health.issues?.length > 0 && (
                        <div className="device-issues">
                          {health.issues.map((issue, i) => (
                            <span key={i} className="device-issue">⚠ {issue}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Register new device */}
              <div className="device-register">
                <h4>➕ Register New Device</h4>
                <div className="settings-field-row">
                  <div className="settings-field">
                    <label>Device ID</label>
                    <input
                      type="text"
                      value={newDevice.device_id}
                      onChange={(e) => setNewDevice((p) => ({ ...p, device_id: e.target.value }))}
                      placeholder="e.g. phone-karthi"
                    />
                  </div>
                  <div className="settings-field">
                    <label>Name</label>
                    <input
                      type="text"
                      value={newDevice.name}
                      onChange={(e) => setNewDevice((p) => ({ ...p, name: e.target.value }))}
                      placeholder="e.g. Karthi's Phone"
                    />
                  </div>
                </div>
                <div className="settings-field-row">
                  <div className="settings-field">
                    <label>Role</label>
                    <select
                      value={newDevice.role}
                      onChange={(e) => setNewDevice((p) => ({ ...p, role: e.target.value }))}
                    >
                      <option value="server">Server</option>
                      <option value="companion">Companion</option>
                      <option value="workstation">Workstation</option>
                      <option value="display">Display</option>
                      <option value="edge">Edge</option>
                    </select>
                  </div>
                  <div className="settings-field">
                    <label>OS</label>
                    <input
                      type="text"
                      value={newDevice.os_type}
                      onChange={(e) => setNewDevice((p) => ({ ...p, os_type: e.target.value }))}
                      placeholder="windows, android, ios..."
                    />
                  </div>
                </div>
                <div className="device-caps-select">
                  <label>Capabilities</label>
                  <div className="cap-toggles">
                    {["compute", "display", "audio", "camera", "location", "mobile", "google"].map((cap) => (
                      <button
                        key={cap}
                        className={`cap-toggle ${newDevice.capabilities.includes(cap) ? "active" : ""}`}
                        onClick={() => toggleCapability(cap)}
                      >
                        {cap}
                      </button>
                    ))}
                  </div>
                </div>
                <button className="settings-save-btn" onClick={registerDevice}>
                  Register Device
                </button>
              </div>
            </div>
          ) : (
            <div className="settings-form">
              {settings[activeTab] &&
                Object.entries(settings[activeTab]).map(([key, value]) => renderField(key, value, typeof value === "number" ? "number" : "text"))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
