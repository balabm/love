import { useState, useEffect } from 'react';
import axios from 'axios';
import './Dashboard.css';

const API = "http://localhost:8000";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [lifeScore, setLifeScore] = useState(null);
  const [loading, setLoading] = useState(true);
  const [moodForm, setMoodForm] = useState({ mood: 7, energy: 7, stress: 3 });
  const [workoutForm, setWorkoutForm] = useState({ type: 'strength', duration: 45 });

  useEffect(() => {
    fetchDashboard();
    fetchLifeScore();
    const interval = setInterval(() => {
      fetchDashboard();
      fetchLifeScore();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await axios.get(`${API}/dashboard`);
      setData(res.data);
    } catch (err) {
      console.error('Dashboard fetch failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchLifeScore = async () => {
    try {
      const res = await axios.get(`${API}/lifescore`);
      setLifeScore(res.data);
    } catch (err) {
      console.error('LifeScore fetch failed:', err);
    }
  };

  const logMood = async () => {
    try {
      await axios.post(`${API}/wellness/mood`, {
        mood_score: moodForm.mood,
        energy: moodForm.energy,
        stress: moodForm.stress,
        emotions: ['happy'],
        context: 'dashboard check-in'
      });
      fetchDashboard();
    } catch (err) {
      console.error('Mood log failed:', err);
    }
  };

  const logWorkout = async () => {
    try {
      await axios.post(`${API}/fitness/workout`, {
        workout_type: workoutForm.type,
        duration: workoutForm.duration,
        exercises: [],
        intensity: 'moderate'
      });
      fetchDashboard();
    } catch (err) {
      console.error('Workout log failed:', err);
    }
  };

  if (loading) return <div className="dashboard-loading">Loading life data...</div>;
  if (!data) return <div className="dashboard-error">Could not load dashboard</div>;

  const { fitness, learning, wellness, tasks, summary } = data;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Life Dashboard</h1>
        <div className="status-badges">
          {summary.positive_statuses.map((s, i) => (
            <span key={i} className="badge success">{s}</span>
          ))}
          {summary.areas_need_attention.map((a, i) => (
            <span key={i} className="badge warning">{a} needs attention</span>
          ))}
        </div>
      </header>

      {/* Life Score Card - Full Width */}
      {lifeScore && (
        <div className="card lifescore-card">
          <div className="lifescore-header">
            <div className="lifescore-main">
              <span className="lifescore-label">Life Score</span>
              <span className={`lifescore-value score-${Math.floor(lifeScore.score / 20)}`}>
                {lifeScore.score}
              </span>
              <span className="lifescore-state">{lifeScore.overall_state}</span>
            </div>
            {lifeScore.breakdown && (
              <div className="lifescore-breakdown">
                {Object.entries(lifeScore.breakdown).map(([domain, score]) => (
                  <div key={domain} className="lifescore-domain">
                    <label>{domain}</label>
                    <div className="lifescore-bar">
                      <div className="lifescore-fill" style={{width: `${Math.min(100, Math.max(0, score * 3))}%`}} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          {lifeScore.recommendations && lifeScore.recommendations.length > 0 && (
            <div className="lifescore-recommendations">
              {lifeScore.recommendations.map((rec, i) => (
                <div key={i} className="recommendation">{rec}</div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="dashboard-grid">
        {/* Fitness Card */}
        <div className="card fitness-card">
          <div className="card-header">
            <span className="card-icon">💪</span>
            <h2>Fitness</h2>
            <span className="streak">🔥 {fitness.streak} day streak</span>
          </div>
          <div className="card-body">
            <div className="stat-row">
              <div className="stat">
                <label>Workouts</label>
                <value>{fitness.workouts_this_week}/{fitness.goal}</value>
              </div>
              <div className="stat">
                <label>Minutes</label>
                <value>{fitness.total_minutes}</value>
              </div>
              <div className="stat">
                <label>Progress</label>
                <value>{fitness.progress_percent}%</value>
              </div>
            </div>
            <p className="insight">{fitness.insight}</p>
            <div className="quick-log">
              <select 
                value={workoutForm.type} 
                onChange={e => setWorkoutForm({...workoutForm, type: e.target.value})}
              >
                <option value="strength">Strength</option>
                <option value="cardio">Cardio</option>
                <option value="mobility">Mobility</option>
              </select>
              <input 
                type="number" 
                value={workoutForm.duration}
                onChange={e => setWorkoutForm({...workoutForm, duration: parseInt(e.target.value)})}
                min="5" max="180"
              />
              <button onClick={logWorkout}>Log</button>
            </div>
          </div>
        </div>

        {/* Learning Card */}
        <div className="card learning-card">
          <div className="card-header">
            <span className="card-icon">📚</span>
            <h2>Learning</h2>
            <span className="streak">🔥 {learning.current_streak} day streak</span>
          </div>
          <div className="card-body">
            <div className="stat-row">
              <div className="stat">
                <label>Weekly Hours</label>
                <value>{learning.weekly_hours}h</value>
              </div>
              <div className="stat">
                <label>Materials</label>
                <value>{learning.active_materials}</value>
              </div>
            </div>
            <p className="insight">{learning.insight}</p>
            {learning.skills && Object.keys(learning.skills).length > 0 && (
              <div className="skills">
                {Object.entries(learning.skills).slice(0, 3).map(([skill, data]) => (
                  <div key={skill} className="skill-tag">
                    {skill}: {data.total_hours.toFixed(1)}h
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Wellness Card */}
        <div className="card wellness-card">
          <div className="card-header">
            <span className="card-icon">🧘</span>
            <h2>Wellness</h2>
          </div>
          <div className="card-body">
            {wellness.avg_mood ? (
              <>
                <div className="stat-row">
                  <div className="stat">
                    <label>Mood</label>
                    <value className={`mood-${Math.round(wellness.avg_mood)}`}>
                      {wellness.avg_mood}/10
                    </value>
                  </div>
                  <div className="stat">
                    <label>Energy</label>
                    <value>{wellness.avg_energy}/10</value>
                  </div>
                  <div className="stat">
                    <label>Stress</label>
                    <value className={wellness.avg_stress > 6 ? 'high-stress' : ''}>
                      {wellness.avg_stress}/10
                    </value>
                  </div>
                </div>
                <p className="insight">{wellness.insight}</p>
              </>
            ) : (
              <p className="no-data">No mood data yet. Quick check-in?</p>
            )}
            <div className="quick-log">
              <input 
                type="range" min="1" max="10" 
                value={moodForm.mood}
                onChange={e => setMoodForm({...moodForm, mood: parseInt(e.target.value)})}
                title="Mood"
              />
              <input 
                type="range" min="1" max="10" 
                value={moodForm.energy}
                onChange={e => setMoodForm({...moodForm, energy: parseInt(e.target.value)})}
                title="Energy"
              />
              <button onClick={logMood}>Log</button>
            </div>
          </div>
        </div>

        {/* Tasks Card */}
        <div className="card tasks-card">
          <div className="card-header">
            <span className="card-icon">✓</span>
            <h2>Tasks</h2>
            <span className="count">{tasks.active_count} active</span>
          </div>
          <div className="card-body">
            <div className="task-stats">
              <div className="priority-bar">
                {tasks.by_priority && Object.entries(tasks.by_priority).map(([p, c]) => (
                  <div key={p} className={`priority-segment ${p}`} style={{flex: c}} title={`${p}: ${c}`} />
                ))}
              </div>
            </div>
            {tasks.due_soon && tasks.due_soon.length > 0 && (
              <div className="due-soon">
                <label>Due Soon</label>
                {tasks.due_soon.slice(0, 3).map((t, i) => (
                  <div key={i} className="due-task">{t.title}</div>
                ))}
              </div>
            )}
            <p className="insight">{tasks.insight}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
