import { useState, useEffect } from 'react';
import api, { API } from '../api';
import './Dashboard.css';

function HealthRing({ value, label, color, size = 56 }) {
  const r = (size - 6) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.min(100, Math.max(0, value));
  const dashoffset = c - (pct / 100) * c;
  return (
    <div className="health-ring">
      <svg width={size} height={size}>
        <circle cx={size/2} cy={size/2} r={r} className="ring-bg" />
        <circle cx={size/2} cy={size/2} r={r} className="ring-fill" stroke={color}
          strokeDasharray={c} strokeDashoffset={dashoffset} />
      </svg>
      <span className="ring-value">{value}</span>
      <span className="ring-label">{label}</span>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [godView, setGodView] = useState(null);
  const [lifeScore, setLifeScore] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [activityStats, setActivityStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [moodForm, setMoodForm] = useState({ mood: 7, energy: 7, stress: 3 });
  const [workoutForm, setWorkoutForm] = useState({ type: 'strength', duration: 45 });

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAll = async () => {
    await Promise.all([fetchDashboard(), fetchGodView(), fetchLifeScore(), fetchSystemStatus(), fetchActivityStats()]);
    setLoading(false);
  };

  const fetchActivityStats = async () => {
    try {
      const res = await api.get('/agi/activity/stats').catch(() => ({ data: null }));
      setActivityStats(res.data);
    } catch (err) {
      console.error('Activity stats fetch failed:', err);
    }
  };

  const fetchDashboard = async () => {
    try {
      const res = await api.get(`/dashboard`);
      setData(res.data);
    } catch (err) {
      console.error('Dashboard fetch failed:', err);
    }
  };

  const fetchGodView = async () => {
    try {
      const res = await api.get(`/dashboard/god-view`);
      setGodView(res.data);
    } catch (err) {
      console.error('God view fetch failed:', err);
    }
  };

  const fetchLifeScore = async () => {
    try {
      const res = await api.get(`/lifescore`);
      setLifeScore(res.data);
    } catch (err) {
      console.error('LifeScore fetch failed:', err);
    }
  };

  const fetchSystemStatus = async () => {
    try {
      const [s, m] = await Promise.all([
        api.get('/agi/autonomy-supervisor/status').catch(() => ({ data: null })),
        api.get('/agi/modules/status').catch(() => ({ data: null })),
      ]);
      if (s.data && m.data) {
        const modules = m.data.modules || {};
        const total = Object.keys(modules).length;
        const ready = Object.values(modules).filter((mod) => mod.state === 'ready').length;
        const degraded = Object.values(modules).filter((mod) => mod.state === 'degraded').length;
        const failed = Object.values(modules).filter((mod) => mod.state === 'failed').length;
        setSystemStatus({
          health_score: s.data.health_score || 0,
          total,
          ready,
          degraded,
          failed,
          ticks: s.data.ticks || 0,
        });
      }
    } catch (err) {
      console.error('System status fetch failed:', err);
    }
  };

  const logMood = async () => {
    try {
      await api.post(`/wellness/mood`, {
        mood_score: moodForm.mood,
        energy: moodForm.energy,
        stress: moodForm.stress,
        emotions: ['happy'],
        context: 'dashboard check-in'
      });
      fetchAll();
    } catch (err) {
      console.error('Mood log failed:', err);
    }
  };

  const logWorkout = async () => {
    try {
      await api.post(`/fitness/workout`, {
        workout_type: workoutForm.type,
        duration: workoutForm.duration,
        exercises: [],
        intensity: 'moderate'
      });
      fetchAll();
    } catch (err) {
      console.error('Workout log failed:', err);
    }
  };

  if (loading) return <div className="dashboard-loading">Loading life data...</div>;
  if (!data) return <div className="dashboard-error">Could not load dashboard</div>;

  const fitness = data.fitness || {};
  const learning = data.learning || {};
  const wellness = data.wellness || {};
  const tasks = data.tasks || {};
  const summary = data.summary || {};

  const interventions = godView?.life_score?.active_interventions || [];
  const work = godView?.work || {};
  const finance = godView?.finance || {};

  return (
    <div className="dashboard">
      {/* Hero — Life Score */}
      <section className="hero">
        <div className="hero-main">
          <div className="hero-score">
            <span className="hero-label">Life Score</span>
            <span className={`hero-number score-${Math.floor((lifeScore?.score || 0) / 20)}`}>
              {lifeScore?.score ?? '—'}
            </span>
            <span className="hero-state">{lifeScore?.overall_state || 'calculating'}</span>
          </div>
          {lifeScore?.breakdown && (
            <div className="hero-breakdown">
              {Object.entries(lifeScore.breakdown).slice(0, 5).map(([domain, score]) => (
                <div key={domain} className="hero-domain">
                  <label>{domain}</label>
                  <div className="hero-bar">
                    <div className="hero-bar-fill" style={{width: `${Math.min(100, Math.max(0, (score || 0) * 3))}%`}} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Status line */}
      <div className="status-line">
        {(summary.positive_statuses || []).map((s, i) => (
          <span key={i} className="status-pill good">{s}</span>
        ))}
        {(summary.areas_need_attention || []).map((a, i) => (
          <span key={i} className="status-pill warn">{a}</span>
        ))}
        {interventions.length > 0 && interventions.slice(0, 2).map((inv, i) => (
          <span key={`inv-${i}`} className="status-pill action">
            {inv.type}: {inv.message}
          </span>
        ))}
      </div>

      {/* Metrics grid */}
      <div className="metrics-grid">
        {/* System Health */}
        <div className="metric-card system">
          <div className="metric-header">
            <span className="metric-icon">🛡️</span>
            <span className="metric-title">System</span>
            <span className="metric-badge" style={{color: systemStatus?.health_score >= 80 ? '#34d399' : systemStatus?.health_score >= 50 ? '#fbbf24' : '#f87171'}}>
              {systemStatus?.health_score ?? 0}%
            </span>
          </div>
          <div className="metric-body">
            <div className="mini-bar-track">
              <div className="mini-bar-fill" style={{
                width: `${systemStatus?.health_score ?? 0}%`,
                background: systemStatus?.health_score >= 80 ? '#34d399' : systemStatus?.health_score >= 50 ? '#fbbf24' : '#f87171'
              }} />
            </div>
            <div className="metric-counts">
              <span>{systemStatus?.ready ?? 0}/{systemStatus?.total ?? 0} ready</span>
              {systemStatus?.failed > 0 && <span className="fail-count">{systemStatus.failed} failed</span>}
            </div>
          </div>
        </div>

        {/* AGI Activity */}
        <div className="metric-card agi">
          <div className="metric-header">
            <span className="metric-icon">🧠</span>
            <span className="metric-title">AGI Today</span>
            <span className="metric-badge" style={{color: activityStats?.trend === 'active' ? '#34d399' : activityStats?.trend === 'warming' ? '#fbbf24' : '#94a3b8'}}>
              {activityStats?.trend || 'idle'}
            </span>
          </div>
          <div className="metric-body">
            <div className="metric-value-row">
              <span className="metric-big">{activityStats?.total ?? 0}</span>
              <span className="metric-sub">actions</span>
            </div>
            <div className="metric-counts">
              {Object.entries(activityStats?.by_component || {}).slice(0, 2).map(([k, v]) => (
                <span key={k}>{v} {k.replace(/_/g, ' ')}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Work */}
        <div className="metric-card work">
          <div className="metric-header">
            <span className="metric-icon">💼</span>
            <span className="metric-title">Work</span>
            <span className="metric-badge" style={{color: work?.overflow > 0 ? '#f87171' : '#34d399'}}>
              {work?.hours_worked?.toFixed(1) ?? '—'}h
            </span>
          </div>
          <div className="metric-body">
            <div className="mini-bar-track">
              <div className="mini-bar-fill" style={{
                width: `${Math.min(100, ((work?.hours_worked || 0) / (work?.work_limit || 8)) * 100)}%`,
                background: work?.overflow > 0 ? '#f87171' : '#34d399'
              }} />
            </div>
            <div className="metric-counts">
              <span>{work?.remaining?.toFixed(1) ?? '—'}h remaining</span>
              {work?.should_stop && <span className="fail-count">Stop working</span>}
            </div>
          </div>
        </div>

        {/* Finance */}
        <div className="metric-card finance">
          <div className="metric-header">
            <span className="metric-icon">💰</span>
            <span className="metric-title">Finance</span>
            <span className="metric-badge" style={{color: (finance?.total_pnl || 0) >= 0 ? '#34d399' : '#f87171'}}>
              {(finance?.total_pnl || 0) >= 0 ? '+' : ''}{(finance?.total_pnl || 0).toFixed(0)}%
            </span>
          </div>
          <div className="metric-body">
            <div className="metric-value-row">
              <span className="metric-big">${(finance?.total_value || 0).toLocaleString()}</span>
              <span className="metric-sub">{(finance?.position_count || 0)} positions</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main grid */}
      <div className="dashboard-grid">
        {/* Fitness */}
        <div className="dash-card">
          <div className="dash-card-top" style={{borderLeftColor: '#34d399'}}>
            <div className="dash-card-header">
              <span className="dash-icon">💪</span>
              <h3>Fitness</h3>
              {fitness.streak > 0 && <span className="dash-streak">{fitness.streak}d streak</span>}
            </div>
            <div className="dash-card-body">
              <div className="dash-stat-row">
                <div className="dash-stat">
                  <span className="dash-num">{fitness.workouts_this_week || 0}<small>/{fitness.goal || 3}</small></span>
                  <span className="dash-label">workouts</span>
                </div>
                <div className="dash-stat">
                  <span className="dash-num">{fitness.total_minutes || 0}</span>
                  <span className="dash-label">minutes</span>
                </div>
                <div className="dash-stat">
                  <span className="dash-num">{fitness.progress_percent || 0}<small>%</small></span>
                  <span className="dash-label">weekly</span>
                </div>
              </div>
              {fitness.insight ? (
                <p className="dash-insight">{fitness.insight}</p>
              ) : (
                <p className="dash-empty">No workouts logged this week. Start with a 20-min session.</p>
              )}
              <div className="dash-action-row">
                <select value={workoutForm.type} onChange={e => setWorkoutForm({...workoutForm, type: e.target.value})}>
                  <option value="strength">Strength</option>
                  <option value="cardio">Cardio</option>
                  <option value="mobility">Mobility</option>
                </select>
                <input type="number" value={workoutForm.duration} onChange={e => setWorkoutForm({...workoutForm, duration: parseInt(e.target.value)})} min="5" max="180" />
                <button onClick={logWorkout}>Log</button>
              </div>
            </div>
          </div>
        </div>

        {/* Learning */}
        <div className="dash-card">
          <div className="dash-card-top" style={{borderLeftColor: '#a78bfa'}}>
            <div className="dash-card-header">
              <span className="dash-icon">📚</span>
              <h3>Learning</h3>
              {learning.current_streak > 0 && <span className="dash-streak">{learning.current_streak}d streak</span>}
            </div>
            <div className="dash-card-body">
              <div className="dash-stat-row">
                <div className="dash-stat">
                  <span className="dash-num">{(learning.weekly_hours || 0).toFixed(1)}<small>h</small></span>
                  <span className="dash-label">this week</span>
                </div>
                <div className="dash-stat">
                  <span className="dash-num">{learning.active_materials || 0}</span>
                  <span className="dash-label">materials</span>
                </div>
              </div>
              {learning.insight ? (
                <p className="dash-insight">{learning.insight}</p>
              ) : (
                <p className="dash-empty">No learning sessions tracked. Add a skill to start.</p>
              )}
              {learning.skills && Object.keys(learning.skills).length > 0 && (
                <div className="dash-tags">
                  {Object.entries(learning.skills).slice(0, 4).map(([skill, data]) => (
                    <span key={skill} className="dash-tag">{skill} <b>{(data.total_hours || 0).toFixed(1)}h</b></span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Wellness */}
        <div className="dash-card">
          <div className="dash-card-top" style={{borderLeftColor: '#f472b6'}}>
            <div className="dash-card-header">
              <span className="dash-icon">🧘</span>
              <h3>Wellness</h3>
            </div>
            <div className="dash-card-body">
              {wellness.avg_mood != null ? (
                <div className="dash-wellness-rings">
                  <HealthRing value={Math.round(wellness.avg_mood || 0)} label="Mood" color="#f472b6" />
                  <HealthRing value={Math.round(wellness.avg_energy || 0)} label="Energy" color="#60a5fa" />
                  <HealthRing value={Math.round(10 - (wellness.avg_stress || 0))} label="Calm" color="#34d399" />
                </div>
              ) : (
                <p className="dash-empty">No mood data. Check in to track emotional trends.</p>
              )}
              {wellness.insight && <p className="dash-insight">{wellness.insight}</p>}
              <div className="dash-action-row">
                <div className="range-group">
                  <label>Mood {moodForm.mood}</label>
                  <input type="range" min="1" max="10" value={moodForm.mood} onChange={e => setMoodForm({...moodForm, mood: parseInt(e.target.value)})} />
                </div>
                <div className="range-group">
                  <label>Energy {moodForm.energy}</label>
                  <input type="range" min="1" max="10" value={moodForm.energy} onChange={e => setMoodForm({...moodForm, energy: parseInt(e.target.value)})} />
                </div>
                <button onClick={logMood}>Log</button>
              </div>
            </div>
          </div>
        </div>

        {/* Tasks */}
        <div className="dash-card">
          <div className="dash-card-top" style={{borderLeftColor: '#fbbf24'}}>
            <div className="dash-card-header">
              <span className="dash-icon">✓</span>
              <h3>Tasks</h3>
              <span className="dash-count">{tasks.active_count || 0} active</span>
            </div>
            <div className="dash-card-body">
              {tasks.by_priority && Object.keys(tasks.by_priority).length > 0 ? (
                <div className="dash-priority-bar">
                  {Object.entries(tasks.by_priority).map(([p, c]) => (
                    <div key={p} className={`dash-priority-seg ${p}`} style={{flex: c}} title={`${p}: ${c}`} />
                  ))}
                </div>
              ) : (
                <p className="dash-empty">No active tasks. The queue is clear.</p>
              )}
              {tasks.due_soon && tasks.due_soon.length > 0 && (
                <div className="dash-due-list">
                  <label>Due soon</label>
                  {tasks.due_soon.slice(0, 3).map((t, i) => (
                    <div key={i} className="dash-due-item">{t.title || 'Untitled'}</div>
                  ))}
                </div>
              )}
              {tasks.insight && <p className="dash-insight">{tasks.insight}</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
