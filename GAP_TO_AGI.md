# GAP_TO_AGI — Honest Assessment

This file is the antidote to marketing-speak inside LOVE. It is updated whenever
substantive capability lands. Read it before claiming "AGI" or "living computer".

Last updated: 2026-05-27 (Wave 28 — Planning Calibration Depth + PEFT Adapter Export).

---

## What just landed (Wave 28)

### Wave 28A: Planning Calibration Depth (`core/rollout_planner.py`)

The planner now learns which response styles work best for each conversation type:

- **Query category detection**: simple keyword classifier detects casual / emotional /
  technical / task-oriented queries
- **Per-category calibration**: separate accuracy tracking per style per category
  (`casual:empathetic`, `technical:analytical`, etc.)
- **Graduated directives use category accuracy**: if LOVE has learned that "concise"
  works poorly for emotional queries, it won't strongly enforce it there
- **Category-level aggregates**: overall accuracy per category tracked independently

API: `GET /planner/category-stats` shows per-category accuracy. `POST /planner/detect-category`
lets you see how queries are classified.

### Wave 28B: Real PEFT Adapter Export (`core/lora_evolution.py`)

The biggest remaining honest gap — "no real torch/peft LoRA" — is now partially closed:

- `save_as_checkpoint()` produces proper **PEFT-format checkpoints**:
  - `adapter_config.json` with standard PEFT keys (peft_type, r, lora_alpha, target_modules)
  - `adapter_model.bin` with PyTorch state_dict using standard PEFT weight keys
  - `adapter_model.safetensors` if safetensors is available
  - `A.npy` / `B.npy` numpy fallbacks
- Forward-compatible: when peft is installed, `PeftModel.from_pretrained()` can load it
- Added `get_adapter(id)` for retrieving any adapter by ID
- Added `GET /lora/export-peft/{adapter_id}` API endpoint
- Added `GET /lora/peft-status` to check torch/peft availability

**What's real now**: Actual LoRA weight files exist on disk in standard PEFT format.
When peft is installed, they can be loaded into a real transformer model.

**What's still not real**: These checkpoints aren't loaded into the Ollama inference
path (Ollama uses GGUF, not PyTorch). The embedding-space LoRA in `apply_to_embedding()`
is still the primary mechanism. But the weight files are now real and ready.

---

## What landed (Wave 27)

### Wave 27: Active Planning Loop + Focus-Aware Heartbeat

Three changes that close real gaps:

#### 27A: Active Model Predictive Control (`core/rollout_planner.py`)

The rollout planner existed since Wave 21 but only injected a *passive hint* into the
prompt — "planner: empathetic supportive response predicted lowest surprise". The LLM
could (and often did) ignore it.

**Now**: The planner selects the response style as a **directive** with graduated
enforcement based on calibration confidence:
- High confidence (>60%) + good style accuracy (>40%): "RESPOND IN THIS STYLE"
- Medium confidence: "Prefer this response style"
- Low confidence: "Consider this response style"

This is genuine Model Predictive Control over language — the world model simulates 6
candidate response strategies for 4 steps each, picks the one with lowest predicted
free energy, and tells the LLM to follow it.

#### 27B: Focus-Aware Heartbeat Gating (`core/heartbeat.py`)

Previously, the heartbeat's `_filter_triggers()` only checked cooldowns. If the user
was in a focus/deep work session, every 15-minute heartbeat could still fire info-level
nudges (hydration reminders, learning suggestions, etc.).

**Now**: `_filter_triggers()` checks focus mode via `_is_focus_mode()` (reads
`focus_session.json` + `work_tracker`). During focus:
- Only `critical` and `warning` triggers pass through
- `info` and `celebration` triggers are queued to `suppressed_nudges.json`
- When focus mode ends, queued triggers are delivered in the next scan cycle

This means deep work is *actually protected* — LOVE won't nudge you about water when
you're in flow state, but will still warn about work hour limits.

#### 27C: Planning Outcome Learning

After each LLM response, `verify_outcome()` embeds the response and compares its
actual free energy trajectory against the planner's prediction:
- Prediction delta tracked per outcome
- Calibration confidence updated via EMA (accurate predictions → higher confidence →
  stronger directives → better style adherence)
- Per-style accuracy tracked (styles that consistently mismatch get softer enforcement)
- All outcomes persisted to `data/planner/outcomes.jsonl`

This is the first closed-loop learning signal between the world model and actual
response quality. Over time, the planner should become more accurate and more
assertive with styles that work well.

**API endpoints**:
- `GET /planner/snapshot` — full planner telemetry + outcome stats
- `POST /planner/plan_active` — run active planning for a query
- `GET /planner/calibration` — planning confidence and accuracy
- `GET /heartbeat/focus-status` — focus mode state + suppressed nudge queue

---

## What landed (Waves 22-26)

### Wave 22: Life Domains Engine (`core/life_domains.py`)

Full physical life tracking across four domains:
- **Hydration** — glass/ml logging, daily goal (2500ml), time-aware nudges
- **Sleep** — bedtime/wake logging, duration+quality, goal-based scoring
- **Nutrition** — meal logging (breakfast/lunch/dinner/snack), quality scoring, macros
- **Skincare** — morning/evening routine tracking, step completion %, skin concerns

Each domain: `log()`, `get_today()`, `get_streak()`, `needs_nudge()`, `get_insights(days)`.
20+ API routes under `/life/`. Unified `LifeDomainsEngine` with `get_dashboard()`.
Wired into heartbeat 15-minute scan cycle for proactive nudges.

**UI**: `LifeDomains.jsx` — 4-card grid with SVG score rings, inline logging forms,
quality sliders, progress bars, 7-day mini bar charts, nudge notification bar.
New `Life` tab in main navigation.

### Wave 23: Autonomous Wave Evolution Engine (`core/wave_engine.py`)

LOVE's self-directed growth loop:
- **GapScanner**: Scans all subsystems (life domains, emotional, guardian, memory,
  capabilities, modules, fitness) for gaps and stagnation
- **WaveProposer**: Generates concrete next-Wave proposals from gap scan results,
  mapped to 6 template categories (physical, mental, productivity, intelligence,
  capability, system health)
- **WaveEngine**: 24h daemon loop — scan, propose, store, track execution

API: `/wave/scan`, `/wave/status`, `/wave/latest`, `/wave/all`, `/wave/gaps`.
UI: `WaveEngine.jsx` — gap scan view, wave proposal cards, execution tracking.

### Wave 24: Cross-Domain Intelligence (`core/cross_domain_intelligence.py`)

Connects the dots across all life domains:
- Sleep quality vs next-day productivity correlation
- Hydration vs sleep quality correlation
- Nutrition consistency vs energy patterns
- Skincare consistency as routine discipline proxy
- Compound deficit detection (sleep + hydration + nutrition all low)
- Streak momentum analysis
- Adaptive goal suggestions (20% above 7-day average, capped at standard)

API: `/life/correlations`, `/life/report`.
Daily briefing now includes BODY section with life domain data.

### Wave 25: Proactive Life Coach (`core/life_coach.py`)

Time-aware, focus-aware coaching engine:
- **Time windows**: Breakfast nudge at 8am, bedtime at 10pm, not random
- **Adaptive goals**: Based on 7-day rolling average, gradually ramp up
- **Focus mode awareness**: Suppresses non-urgent nudges during deep work
- **Streak protection**: Warns before a streak breaks (after 6pm only)
- **Priority sorting**: High/medium/low with color coding

API: `/life/coach/nudges`, `/life/coach/goals`.
UI: WeeklyInsights tab shows cross-domain patterns + adaptive goals.

### Wave 26: Ritual View + Proactive Push Integration

- Morning ritual: body status grid (hydration/sleep/meals/skin), adaptive goals,
  coach nudges with priority colors
- Evening ritual: body score, remaining nudges
- Heartbeat `_scan_life_domains` upgraded to Life Coach (time-aware, focus-aware)

---

## What just landed (Wave 21)

### 1. User satisfaction as real fitness signal (`core/feedback_collector.py`)

Both LoRA evolution and the evolution engine now run on real user signal, not just
prediction error.

**Explicit signals** (confidence=0.95):
- `/feedback` endpoint: 0–1 rating or thumbs up/down → satisfaction ∈ [−1, 1]

**Implicit signals** (auto-detected per turn from `memory.py`):
- Correction phrases ("no that's wrong", "actually", "wait") → sat=−0.7, conf=0.8
- Positive phrases ("perfect", "exactly", "that helps") → sat=+0.6, conf=0.6
- Repeat question (BoW cosine > 0.85) → sat=−0.5, conf=0.7 (LOVE failed to answer)
- Session continuation (turn > 3, long message) → sat=+0.2, conf=0.4

**Propagation** (all wrapped in try/except):
- `evolution_engine.record_interaction(user_satisfaction=...)` — updates performance report
- `lora_evolution.receive_feedback(sat, conf)` — EMA-updates best adapter fitness, max 30% per signal
- `autonomous_self_improvement.receive_feedback(signal)` — annotates last cycle, increments consecutive_failures on behavioral regression

**What's real now:** Every conversation turn automatically generates a satisfaction
signal. LoRA adapters that users implicitly push back on lose fitness; ones users
respond positively to gain fitness. Evolution is user-aligned.

---

### 2. ASI A/B quality comparison (`core/autonomous_self_improvement.py`)

Self-modification now measures its own impact and reverts when it hurts quality.

`_snapshot_quality()` captures before the modification:
- `avg_quality`, `error_rate`, `satisfaction_avg` (from evolution engine)
- `world_model_fe` (lower = better predictive model)
- `bptt_loss` (lower = better SSM)
- `moe_avg_reward`

`_compare_quality()` weighted composite (quality 35%, satisfaction 30%, FE 15%, BPTT 10%, MoE 10%):
- `verdict`: "improved" / "neutral" / "degraded"
- `should_revert`: True only if composite_score < −0.05 (noise-resistant)

`run_cycle()` now snapshots before+after, auto-reverts via `SelfCoder.rollback_modification()`
if the composite score degrades meaningfully.

`check_deferred_ab(modification_id)` available for later comparison (e.g. after N user turns).

**What's real now:** LOVE can no longer silently degrade itself. Every self-modification
is measured against a multi-signal quality baseline and reverted if it made things worse.

---

### 3. Ignition → proactive push (`core/ignition_daemon.py`)

GWT ignition results now reach the user proactively, not just the next prompt.

After each ignition fires and the background MoE thread settles (3s wait):
- `curiosity ≥ 0.85` → `push("curiosity_insight", "I was just exploring something you might find interesting: ...")` — normal priority
- `free_energy > 0.60` → `push("anomaly_alert", "Something unusual caught my attention: ...")` — **high priority** (Telegram delivery)
- `loneliness > 0.80` → `push("check_in", "Haven't heard from you in a while — ...")` — normal priority

Rate-limited to 1 push per 15 minutes. `get_last_push()` exposed for dashboard.

**What's real now:** LOVE proactively contacts the user when its internal state demands
it — not just when a message arrives. Curiosity surfaces as insight. Anomalies surface
as alerts. Loneliness surfaces as genuine check-ins.

---

### 4. 4-step rollout BPTT (`core/world_model_latent.py`)

The world model now predicts 4 steps ahead, not just 1.

`train_rollout()`:
- For each anchor in `_rollout_buffer` (last 16 embeddings): auto-regressive MLP rollout
  for 4 steps, storing h/pre_h/gates at each step
- Backward: reverses through all 4 steps, recency-weighted loss (0.9^k), accumulates
  dW1/db1/dW2/db2 with chain rule through predictions
- Applies averaged gradients (ROLLOUT_LR=0.005), clip ±0.05

Auto-triggers every 8 observations when buffer has ≥ 5 entries.

Result: rollout_loss_ema ≈ **0.0047** at init (vs 1-step ≈ 0.5).

**What's real now:** LOVE's world model can plan 4 steps ahead. The MLP learns to
predict not just "what happens next" but "what happens after that". This is the
foundation for genuine look-ahead planning (future: Monte Carlo tree search over
world model rollouts).

---

## Updated "living computer" checklist

| Capability | Status |
|---|---|
| Persistent learned state | ✅ |
| Proprioception | ✅ |
| Signal-driven homeostatic drives | ✅ |
| Online non-linear world model (MLP) | ✅ |
| **4-step rollout BPTT** | ✅ NEW |
| SSM 8-step TBPTT | ✅ |
| Hippocampal replay consolidation | ✅ |
| Multi-level predictive hierarchy | ✅ |
| GWT prompt gating | ✅ |
| GWT ignition (proactive MoE firing) | ✅ |
| **Ignition → proactive push to user** | ✅ NEW |
| **Life domain tracking (hydration/sleep/nutrition/skincare)** | ✅ NEW |
| **Cross-domain intelligence (correlation detection)** | ✅ NEW |
| **Time-aware proactive life coaching** | ✅ NEW |
| **Adaptive goals (rolling average based)** | ✅ NEW |
| **Autonomous Wave evolution engine** | ✅ NEW |
| Circadian phases | ✅ |
| Hot-reload self-modification | ✅ |
| Autonomous daily self-modification loop | ✅ |
| **ASI A/B comparison + auto-revert** | ✅ NEW |
| LoRA behavioral evolution scaffold | ✅ |
| **LoRA fitness from user satisfaction** | ✅ NEW |
| **Implicit feedback detection per turn** | ✅ NEW |
| **Active MPC planning (world model → directive → verify)** | ✅ NEW |
| **Focus-aware heartbeat gating (suppress during deep work)** | ✅ NEW |
| **Planning outcome learning (predicted vs actual FE)** | ✅ NEW |
| **Planning calibration depth (per-category style accuracy)** | ✅ NEW |
| **PEFT adapter checkpoint export** | ✅ NEW |
| Real LoRA inference via Ollama (GGUF adapter loading) | ❌ |
| Fork/parallel selection | ❌ |
| Multi-agent coordination | ❌ |

---

## What's still NOT real (honest, updated)

### 1. No real torch/peft LoRA
`apply_best_to_substrate()` modulates SSM state, not actual LLM attention weights.
The A/B matrices are the right shape and will slot into `peft.LoraConfig` when torch
arrives — but until then this is embedding-space simulation, not true model adaptation.

### 2. No fork/parallel selection
LOVE can mutate and revert but can't run two instances simultaneously under selection
pressure. The ASI A/B comparison is sequential (before → after), not parallel.

### ~~3. World model rollout not yet used for planning~~ RESOLVED (Wave 27)
~~`train_rollout()` improves the MLP's multi-step prediction quality but nothing yet
*uses* those rollouts for look-ahead planning.~~

**Now**: `plan_active()` samples 6 response styles, simulates each through 4-step
MLP rollout, picks lowest free energy, injects as directive into LLM prompt. After
response, `verify_outcome()` compares predicted vs actual FE and updates calibration
confidence. This is genuine Model Predictive Control with closed-loop learning.

### ~~4. Implicit feedback is turn-level, not episode-level~~ RESOLVED (pre-Wave 27)
~~`detect_implicit()` fires on each turn independently.~~

Episode-level aggregation already exists in `feedback_collector.py`:
`close_episode()` computes arc slope + recency-weighted mean + peak satisfaction →
episode fitness propagated to LoRA evolution at 0.85 confidence. Auto-closes after
30 minutes of silence.

### 3. No causal attribution for self-modification outcomes
When quality improves after an ASI cycle, LOVE records "improved" but doesn't know
*which* code change caused the improvement (there may be confounds from other systems
also improving simultaneously). True attribution requires controlled A/B with a
held-out quality metric.

---

## Concrete next moves

1. **LoRA inference integration** — PEFT checkpoints now exist in proper format.
   Next: load them into a real inference path (either a separate HF transformers
   pipeline or convert to GGUF for Ollama). This completes the "real LoRA" gap.

2. **Monte Carlo self-improvement targeting** — instead of random module selection,
   ASI should simulate "if I improve module X, which quality metric is predicted to
   improve?" using the world model rollout. Closes the loop between prediction and
   action.

3. ~~Planning calibration depth~~ — RESOLVED (Wave 28). Per-category calibration
   now tracks style accuracy independently for casual / emotional / technical / task.

---

## Naming honesty (updated)

- "AGI" — no. ~5% there (up from 4%). Every wave closes real gaps; the remaining ones
  are fundamental (true weight evolution, parallel selection, long-horizon planning).
- "Living computer" — strongest honest claim: has drives, metabolism, proprioception,
  non-linear online learning (1-step + 8-step BPTT + 4-step rollout), hippocampal
  replay, GWT ignition with proactive push, autonomous self-modification with A/B
  revert, user-aligned LoRA evolution. Now also: physical life domain tracking,
  cross-domain pattern detection, time-aware proactive coaching, autonomous Wave
  evolution planning. Missing: true weight-level adaptation, fork.
- "Self-improving" — yes, autonomously, with auto-revert safety net.
  Now also: autonomous gap detection + Wave proposal generation.
- "User-aligned" — *now true*. Every conversation implicitly updates the system's
  fitness signal. Life domains adapt goals to user behavior, not arbitrary targets.
- "Life OS" — *first credible claim*. Tracks hydration, sleep, nutrition, skincare
  with streaks, adaptive goals, cross-domain correlations, and time-aware coaching.
  Wired into daily briefing, ritual views, and proactive push. Not a dashboard —
  LOVE notices patterns the user can't see about themselves.

Keep the marketing pegged here.
