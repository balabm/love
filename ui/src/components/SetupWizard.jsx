import { useState, useEffect } from "react";
import api, { API } from "../api";
import "./SetupWizard.css";

const ACCENT = {
  google: "red",
  microsoft: "blue",
  github: "orange",
  finance: "green",
  telegram: "purple",
  phone: "pink",
  browser: "cyan",
  briefing: "teal",
};

function FieldInput({ field, value, onChange }) {
  const [show, setShow] = useState(false);
  const isSecret = field.is_secret || field.secret;
  const type = isSecret && !show ? "password" : "text";

  return (
    <div className="swz-field">
      <label className="swz-field-label">
        {field.label}
        {field.hint && <span className="swz-hint">{field.hint}</span>}
      </label>
      <div className="swz-input-wrap">
        <input
          type={type}
          className="swz-input"
          placeholder={field.placeholder || field.key}
          value={value}
          onChange={e => onChange(e.target.value)}
          autoComplete="off"
        />
        {isSecret && (
          <button className="swz-show-btn" onClick={() => setShow(s => !s)} type="button">
            {show ? "hide" : "show"}
          </button>
        )}
      </div>
    </div>
  );
}

function IntegrationCard({ integration, onSave }) {
  const accent = ACCENT[integration.id] || "blue";
  const [values, setValues] = useState({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [authing, setAuthing] = useState(false);
  const [authResult, setAuthResult] = useState(null);
  const [expanded, setExpanded] = useState(false);

  const allSet = integration.fields.every(f => f.is_set || values[f.key]);
  const anySet = integration.fields.some(f => f.is_set);

  const save = async () => {
    setSaving(true);
    setSaved(false);
    const updates = {};
    for (const f of integration.fields) {
      if (values[f.key] !== undefined && values[f.key] !== "") {
        updates[f.key] = values[f.key];
      }
    }
    try {
      await api.post(`/neural/setup/save`, { updates });
      setSaved(true);
      setValues({});
      onSave();
      setTimeout(() => setSaved(false), 3000);
    } catch (e) { console.error("[Setup] save failed:", e); }
    setSaving(false);
  };

  const triggerAuth = async () => {
    if (!integration.auth_endpoint) return;
    setAuthing(true);
    setAuthResult(null);
    try {
      const res = await api.post(integration.auth_endpoint);
      setAuthResult(res.data);
    } catch (e) {
      console.error("[Setup] auth trigger failed:", e);
      setAuthResult({ success: false, error: "Request failed" });
    }
    setAuthing(false);
  };

  return (
    <div className={`swz-card swz-card-${accent}`}>
      <div className="swz-card-header" onClick={() => setExpanded(e => !e)}>
        <div className="swz-card-icon">{integration.icon}</div>
        <div className="swz-card-info">
          <div className="swz-card-name">
            {integration.label}
            <span className={`swz-status ${allSet ? "swz-status-done" : anySet ? "swz-status-partial" : "swz-status-none"}`}>
              {allSet ? "configured" : anySet ? "partial" : "not set"}
            </span>
          </div>
          <div className="swz-card-desc">{integration.description}</div>
        </div>
        <span className="swz-chevron">{expanded ? "▲" : "▼"}</span>
      </div>

      {expanded && (
        <div className="swz-card-body">
          {/* Fields */}
          {integration.fields.map(field => (
            <FieldInput
              key={field.key}
              field={field}
              value={values[field.key] !== undefined ? values[field.key] : (field.is_set ? field.current_value : "")}
              onChange={v => setValues(prev => ({ ...prev, [field.key]: v }))}
            />
          ))}

          {/* Docs link */}
          {integration.docs_url && (
            <div className="swz-docs">
              Setup guide: <a href={integration.docs_url} target="_blank" rel="noreferrer">{integration.docs_url}</a>
            </div>
          )}

          {/* Save + Auth buttons */}
          <div className="swz-actions">
            <button
              className={`swz-save-btn${saving ? " swz-saving" : ""}${saved ? " swz-saved" : ""}`}
              onClick={save}
              disabled={saving}
            >
              {saved ? "Saved!" : saving ? "Saving..." : "Save to .env"}
            </button>
            {integration.auth_endpoint && (
              <button
                className={`swz-auth-btn${authing ? " swz-authing" : ""}`}
                onClick={triggerAuth}
                disabled={authing}
              >
                {authing ? "Starting..." : integration.auth_label || "Authorize"}
              </button>
            )}
          </div>

          {/* Auth result */}
          {authResult && (
            <div className={`swz-auth-result ${authResult.success ? "swz-auth-ok" : "swz-auth-err"}`}>
              {authResult.success ? (
                <>
                  {authResult.message && <div>{authResult.message}</div>}
                  {/* Microsoft device code flow */}
                  {authResult.user_code && (
                    <div className="swz-device-code">
                      <div className="swz-device-code-title">Device Code Auth</div>
                      <div>
                        Go to:{" "}
                        <a href={authResult.verification_uri} target="_blank" rel="noreferrer">
                          {authResult.verification_uri}
                        </a>
                      </div>
                      <div className="swz-code-value">{authResult.user_code}</div>
                      <div className="swz-code-hint">Enter this code in the browser to authorize LOVE</div>
                      {authResult.message && <div className="swz-code-msg">{authResult.message}</div>}
                    </div>
                  )}
                </>
              ) : (
                <div>{authResult.error || "Authorization failed"}</div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function SetupWizard() {
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadIntegrations = async () => {
    try {
      const res = await api.get(`/neural/setup/integrations`);
      setIntegrations(res.data.integrations || []);
      setError(null);
    } catch (e) {
      console.error("[Setup] load integrations failed:", e);
      setError("Backend offline — is LOVE running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIntegrations();
  }, []);

  const configuredCount = integrations.filter(i => i.fields.every(f => f.is_set)).length;

  if (loading) {
    return <div className="swz-panel"><div className="swz-loading">Loading setup wizard...</div></div>;
  }

  if (error) {
    return <div className="swz-panel"><div className="swz-offline">{error}</div></div>;
  }

  return (
    <div className="swz-panel">
      <div className="swz-header">
        <div>
          <h2>Setup Wizard</h2>
          <div className="swz-subtitle">Connect LOVE to your accounts and devices</div>
        </div>
        <div className="swz-progress-wrap">
          <div className="swz-progress-label">{configuredCount}/{integrations.length} configured</div>
          <div className="swz-progress-bar">
            <div
              className="swz-progress-fill"
              style={{
                width: `${integrations.length ? (configuredCount / integrations.length) * 100 : 0}%`,
              }}
            />
          </div>
        </div>
      </div>

      <div className="swz-note">
        Changes are written to <code>.env</code> immediately. Restart the server to apply LLM model changes.
        Auth tokens (Google/Microsoft) are stored separately in <code>data/</code>.
      </div>

      <div className="swz-list">
        {integrations.map(i => (
          <IntegrationCard key={i.id} integration={i} onSave={loadIntegrations} />
        ))}
      </div>
    </div>
  );
}
