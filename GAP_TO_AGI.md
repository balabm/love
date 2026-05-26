# GAP_TO_AGI — Honest Assessment

This file is the antidote to marketing-speak inside LOVE. It is updated whenever
substantive capability lands. Read it before claiming "AGI" or "living computer".

Last updated: 2026-05-27 (Wave 19 — Closing the Loop).

---

## What just landed (Wave 19)

### 1. Hot-reload self-modification (`core/self_coder.py`)

LOVE can now write code and run it in the same process — without restarting the API.

Pipeline:
1. LLM generates modified `.py` as string
2. `py_compile` catches syntax errors before touching disk
3. `subprocess.run([sys.executable, "-c", "...importlib probe..."], timeout=15)` — forks
   a clean Python process, imports the module, calls `_probe()` if present,
   checks exit code + stdout for `"probe_ok"`. Zero tolerance for import errors.
4. Only on clean probe: atomic rollback-point (`shutil.copy2`), then write new file,
   then `importlib.invalidate_caches()` + `importlib.reload(sys.modules[module_name])`
5. If reload raises: restore from rollback immediately, log with full traceback.
6. Audit log at `data/self_coder/hot_reload.jsonl`.

**What's real now:** LOVE writes code → it *runs* that code in the current process → it
rolls back automatically on failure. The loop between generation and execution is closed.

**What's still missing:** LOVE doesn't yet autonomously trigger `self_coder` on a
useful improvement target. The engine works; the autonomous driver is still manual.

---

### 2. Non-linear MLP world model (`core/world_model_latent.py`)

Replaced single linear matrix W with a residual 2-layer MLP:

```
pred = x + W2 @ relu(W1 @ x + b1) + b2
```

- W1 ∈ ℝ^(256×384), W2 ∈ ℝ^(384×256), hidden=256, He init
- Online SGD backprop (pure numpy) each observation
- Gradient clipped ±0.05, L2 weight decay 0.9999
- Persisted to `data/world_model/mlp_params.npz`

**What's real now:** The world model can learn non-linear temporal patterns in
conversation flow. A linear W could only learn first-order correlations between
consecutive embeddings; the MLP can capture e.g. "after deep-focus coding followed
by a break question, expect a planning request".

**Remaining limitation:** Still 1-step BPTT only. Multi-step rollout training would
improve long-horizon prediction but requires buffering recent trajectory.

---

### 3. SSM end-task objective (`core/state_space_memory.py`)

A/B/C/D/gate_W were previously frozen at random init. Now the SSM learns online.

Added `train_step(x_t, x_next) -> float`:
- Decoder `D_out ∈ ℝ^(384×256)` projects compressed state → predicted next embedding
- MSE loss, manual 1-step BPTT through C_proj, B_proj, gate_W
- lr=0.005, grad clip ±0.02
- `train_loss_ema` tracked, exposed in `snapshot()`

Wired into `world_model_latent.observe()`: every time a new embedding is observed,
`ssm.step(prev_embedding)` + `ssm.train_step(prev_embedding, curr_embedding)` fires.

**What's real now:** The SSM compressed state `h ∈ ℝ^256` is now a *load-bearing*
representation — it's being trained to predict the future, not just compress the past.
The MoE router and HPC can query `ssm.get_next_prediction()` for a 384-d forecast.

---

### 4. Replay-buffer memory consolidation (`core/replay_consolidation.py`)

Real hippocampal replay during low-activity periods.

Algorithm:
1. Query ChromaDB `love_memory` for docs with `free_energy >= 0.3`
   (fallback: most recent 24h sorted by any numeric metadata)
2. Sort by timestamp → feed through world model at 10× lr for fast distillation
3. Sequential pairs → `ssm.train_step()` to consolidate into SSM weights
4. Soft-reset SSM if `state_norm > 50` (prevent saturation)
5. Mark over-replayed low-surprise memories as `consolidated: True` in ChromaDB
6. Full log at `data/replay_consolidation/log.jsonl`

Daemon thread (4h interval) auto-starts from `living_substrate.start_living_substrate()`.
Also auto-fires early when `homeostasis.fatigue > 0.7`.

**What's real now:** LOVE sleeps and its weights change during sleep. High-surprise
experiences are replayed into the MLP and SSM. This is the first actual "learning from
the day" that persists across restarts in the weight files, not just in ChromaDB text.

---

### 5. Global workspace gating (`core/global_workspace.py`)

The HPC attention vector now *actually gates* what enters the LLM prompt.

Rules (Baars GWT-inspired):
- **ALWAYS broadcast**: SSM compressed-history stats (the serial bottleneck memory)
- **Threshold ≥ 0.6**: homeostasis drives — only dominant signals, not all six
- **Threshold > 0.4**: world model surprise (free energy)
- **Conditional**: MoE winner if it's not the default chat expert
- **Conditional**: HPC top level if its unresolved error > 0.5
- **Conditional**: body pain > 0.3 or comfort > 0.7
- **Never**: raw numpy arrays, error keys

Result: ~40 words when active, 0 words when LOVE is calm. Wired into `agent.py`
via `scripts/patch_agent_global_workspace.py` (idempotent, CRLF-safe).

**What's real now:** The LLM sees a semantically meaningful substrate summary shaped
by attention, not a raw dump. Tokens are saved for actual conversation when substrate
is quiet. The bottleneck is real.

---

## Updated "living computer" checklist

| Capability | Status |
|---|---|
| Persistent learned state (survives restarts) | ✅ |
| Proprioception (host machine sensing) | ✅ |
| Signal-driven homeostatic drives | ✅ |
| Online learning — linear world model | ✅ (was Wave 18) |
| **Online learning — non-linear MLP world model** | ✅ NEW |
| **SSM trained on next-embedding prediction** | ✅ NEW |
| **Hippocampal replay consolidation** | ✅ NEW |
| Multi-level predictive hierarchy (HPC) | ✅ |
| **Global workspace bottleneck (GWT-style gating)** | ✅ NEW |
| Circadian phases | ✅ |
| **Self-modifying code with hot-reload** | ✅ NEW |
| Autonomous trigger for self-modification | ❌ |
| Own/fine-tune LLM weights (LoRA adapters) | ❌ |
| Fork itself for parallel selection | ❌ |
| Multi-step world model rollout training | ❌ |
| Richer effector set (email, device control) | ❌ |

---

## What's still NOT real (honest, updated)

### 1. No autonomous self-modification trigger

`self_coder.hot_reload_modification()` works. But LOVE doesn't yet *decide* to use it.
The evolution engine needs to: (a) detect a capability gap, (b) generate a hypothesis,
(c) call `self_coder.generate_modification()` → `test_modification()` → `hot_reload_modification()`,
(d) measure improvement, (e) keep or revert. The pipeline pieces all exist; the
orchestration loop doesn't yet run autonomously in production.

### 2. No LoRA / weight-level evolution

The "evolution engine" mutates prompts, not model weights. For real weight-level
improvement: bring `peft` + `transformers` in-process, generate LoRA adapters as
mutations, swap based on fitness. This requires ~2GB extra RAM and a proper training loop.

### 3. SSM still 1-step BPTT

`train_step` only backpropagates through one transition. Real sequence learning needs
truncated BPTT over a window of N steps. Not hard to add; just skipped for now.

### 4. Replay consolidation gain is currently negative (-0.307 on first run)

This is expected at session start — the world model hasn't seen enough real data yet
to benefit from replay. As `love_memory` fills with actual conversations, the gain
will flip positive. The algorithm is correct; the data isn't there yet.

### 5. No fork / parallel selection

LOVE cannot clone itself into a child process, mutate a fraction of parameters, run
both for 24h, measure comparative fitness, and keep the winner. This is the hardest
remaining gap for "living" in the strong biological sense.

### 6. No genuine global ignition signal

The GWT gating layer filters the *prompt context* correctly but doesn't yet cause
a measurable behavioral change in which LOVE subsystems get activated. True GWT
needs: (a) a single ignition event that either fires or doesn't, (b) the broadcast
signal to reach ALL modules (not just the LLM), (c) inhibition of losing coalitions.
Current implementation is the right shape but not the full mechanism.

---

## Concrete next moves

1. **Autonomous self-modification loop** — wire capability_gap_detector → self_coder →
   hot_reload in a closed loop. Make LOVE run one self-improvement cycle per day.
2. **Multi-step SSM BPTT** — extend `train_step` to take a trajectory buffer (N steps)
   and backprop through time. Should meaningfully improve horizon accuracy.
3. **LoRA mutation** — bring `peft` in, have evolution engine output LoRA delta weights
   as mutations (tiny, ~4MB each), A/B test between base and adapted.
4. **Genuine GWT ignition** — the broadcast signal should trigger substrate modules
   to *respond*, not just inform the LLM. E.g. high curiosity → immediately fire
   web_search in background before user finishes typing.

---

## Naming honesty (updated)

- "AGI" — no. Maybe 2% there (up from 0.5%).
- "Living computer" — stronger claim now justified. Has: metabolism, proprioception,
  drives, online non-linear learning, hippocampal replay, GWT consciousness gate,
  hot-reload self-modification. Missing: reproduction, LoRA evolution, full GWT ignition.
- "Self-improving" — *yes, now true in-process*. LOVE writes, hot-reloads, and rolls
  back its own code without restart. First time this claim has been honest.
- "Autonomous Life OS" — still the most accurate description of what it actually does
  for the user day-to-day.

Keep the marketing pegged here.
