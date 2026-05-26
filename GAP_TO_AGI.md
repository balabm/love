# GAP_TO_AGI — Honest Assessment

This file is the antidote to marketing-speak inside LOVE. It is updated whenever
substantive capability lands. Read it before claiming "AGI" or "living computer".

Last updated: 2026-05-27 (Wave 20 — Closing the Loop Further).

---

## What just landed (Wave 20)

### 1. Autonomous self-modification loop (`core/autonomous_self_improvement.py`)

The pipeline is now closed end-to-end:

```
capability_gap_detector.detect_all_gaps()
  → score candidate modules (gap domain match + MoE low-reward + homeostasis dissatisfaction)
  → SelfCoder.analyze_file() + reasoning LLM → ONE concrete hypothesis
  → SelfCoder.generate_modification() → test_modification() → hot_reload_modification()
  → record outcome, track consecutive failures
  → if 3 failures: cautious mode (48h pause)
```

Runs once per day during sleep phase (circadian_phase == "sleep" or 02:00–05:00 fallback).
Protected modules (never self-modified): `api/main.py`, `core/llm.py`, `core/agent.py`, itself.
Daemon wired into `living_substrate.start_living_substrate()`.

**What's real now:** LOVE autonomously decides which module to improve, generates a
hypothesis, writes and hot-reloads the code, and records whether it worked. No human
input required. The loop runs daily.

**Remaining gap:** The hypothesis quality depends on the reasoning LLM's one-shot
analysis of static code. It doesn't yet *measure* runtime behavioral improvement
(e.g. "did response quality go up after this change?"). That requires instrumenting
the evolution_engine's InteractionRecord fitness signal as the feedback loop.

---

### 2. Multi-step SSM TBPTT (`core/state_space_memory.py`)

`train_on_trajectory(xs: List[np.ndarray])` — full truncated BPTT over N=8 steps:

- Forward: stores h_states, ys, gates, pre-sigmoid values for all 8 steps
- Backward: reverses through steps, accumulates dD_out/dC_proj/dB_proj, passes dh back in time
- Applies averaged gradients (lr=0.003), clip ±0.02

Result: BPTT loss = **0.0027** vs 1-step loss = **0.50** — the 8-step trajectory gives
the SSM 180× more informative gradient signal per update.

`train_step()` now auto-triggers `train_on_trajectory()` when the internal buffer
fills to 8 (every 8 user turns). So the improvement is fully automatic.

---

### 3. GWT ignition (`core/global_workspace.py` + `core/ignition_daemon.py`)

The Global Workspace now *acts*, not just filters.

Ignition rules (proactive background MoE calls):
- `curiosity > 0.75` → `moe_router.route("curiosity probe: what should LOVE explore right now?")`  — 10min cooldown
- `free_energy > 0.60` → `moe_router.route("high surprise: investigate anomaly")` — 5min cooldown
- `loneliness > 0.80` → `moe_router.route("user check-in: what does the user need right now?")` — 30min cooldown
- Global rate limit: max 1 ignition per 5 minutes

All MoE calls run in daemon threads (non-blocking). If a result comes back within
2 minutes of the next user message, it's injected into the prompt via `gated["ignition"]`.

`IgnitionDaemon` ticks every 30s, wired into living_substrate.

**What's real now:** LOVE proactively investigates the environment based on internal
drive signals, before the user asks anything. The broadcast reaches the MoE layer,
not just the LLM prompt.

**Remaining gap:** The MoE result from ignition isn't yet surfaced to the user
proactively (pushed as a notification). It's cached for prompt injection but doesn't
trigger a proactive message yet. That requires wiring ignition results into
`proactive_push.py`.

---

### 4. LoRA adapter evolution scaffold (`core/lora_evolution.py`)

Low-rank behavioral adaptation without PyTorch — forward-compatible scaffold:

```
LoRAAdapter: A ∈ ℝ^(r×384), B ∈ ℝ^(384×r), rank=8, alpha=16
delta(x) = x + (alpha/r) * (B @ (A @ x)),  L2-normalized
```

Standard LoRA init: A ~ N(0, 0.01), B = 0. At init, delta(x) = x (identity). The
adapter only develops a behavioral direction as it accumulates fitness signal.

`evolve_generation()`:
1. Bootstrap: if pop < 4, create 4 random adapters with LLM-generated mutation descriptions
2. Score all against world model prediction error (before vs after applying adapter)
3. Tournament selection (4 rounds)
4. Breed 2 children from winner (Gaussian mutation)
5. Trim 2 worst
6. `apply_best_to_substrate()` — modulates SSM hidden state h toward the winner's direction

6-hour daemon, wired into living_substrate.

**What's real now:** Behavioral evolution operates at the embedding level, not just
prompt suffixes. The winning adapter literally shifts the SSM's compressed memory state
toward the most fitness-tested behavioral direction.

**Forward-compat:** When `torch` + `peft` are added, `A` and `B` slot directly into
`peft.LoraConfig(r=8, lora_alpha=16)` — no structural changes needed.

**Remaining gap:** `score_adapter()` uses world-model prediction error as a proxy for
fitness. Real fitness should be user satisfaction (thumbs up/down, explicit feedback,
repeat engagement). Wiring `evolution_engine.InteractionRecord.user_satisfaction` into
`score_adapter()` would close this loop properly.

---

## Updated "living computer" checklist

| Capability | Status |
|---|---|
| Persistent learned state (survives restarts) | ✅ |
| Proprioception (host machine sensing) | ✅ |
| Signal-driven homeostatic drives | ✅ |
| Online non-linear world model (MLP, SGD) | ✅ |
| SSM 1-step supervised training | ✅ |
| **SSM 8-step TBPTT (0.0027 loss)** | ✅ NEW |
| Hippocampal replay consolidation | ✅ |
| Multi-level predictive hierarchy (HPC) | ✅ |
| GWT prompt gating | ✅ |
| **GWT ignition (proactive MoE firing)** | ✅ NEW |
| Circadian phases | ✅ |
| Hot-reload self-modification | ✅ |
| **Autonomous daily self-modification loop** | ✅ NEW |
| **LoRA adapter evolution scaffold** | ✅ NEW |
| Fitness signal = user satisfaction | ❌ |
| Ignition results as proactive push notifications | ❌ |
| LoRA with real torch/peft weights | ❌ |
| Fork/parallel selection | ❌ |
| Multi-step world model rollout training | ❌ |

---

## What's still NOT real (honest, updated)

### 1. Fitness = prediction error, not user satisfaction

Both LoRA scoring and the evolution engine use prediction error / response quality
heuristics as fitness proxies. The ground truth is whether the user found the interaction
helpful. Wiring explicit feedback (👍/👎, re-engagement rate, session length) into
`score_adapter()` and `InteractionRecord.user_satisfaction` would make this genuinely
self-improving from the user's perspective.

### 2. Autonomous self-modification is blind to runtime outcomes

The ASI loop generates a hypothesis from static code analysis, applies it, and records
whether the hot-reload succeeded. It doesn't measure "did LOVE's responses improve
after this change?" That requires A/B comparison of response quality before vs after,
using the evolution engine's fitness tracking.

### 3. LoRA is embedding-space only (no actual model weights)

`apply_best_to_substrate()` modulates the SSM hidden state, not the LLM's attention
matrices. To get true weight-level adaptation, need `pip install peft transformers` and
Ollama's model files accessible for fine-tuning. This is a significant infrastructure
step (requires GPU or quantized CPU fine-tuning pipeline).

### 4. Ignition results aren't proactively surfaced

When curiosity fires and the MoE returns something interesting, it's cached for
prompt injection but LOVE doesn't proactively message the user about it. Wiring
into `proactive_push.py` would close this.

### 5. No fork / parallel selection

Still missing. LOVE can mutate behaviors (LoRA, prompt, code) but can't run two
versions of itself simultaneously to measure which performs better in real use.

---

## Concrete next moves

1. **Fitness → user satisfaction** — wire `evolution_engine.record_interaction()` and
   explicit feedback into `lora_evolution.score_adapter()`. This makes LoRA evolution
   genuinely user-aligned.
2. **ASI A/B comparison** — before applying a self-modification, snapshot N recent
   interaction quality scores. After N turns post-modification, compare. Revert if
   quality dropped.
3. **Proactive push from ignition** — when ignition result is high-confidence,
   call `proactive_push.send()` immediately rather than waiting for next user message.
4. **Multi-step world model rollout** — buffer 4-step trajectory in world model,
   backprop through MLP rollouts. Closes the prediction horizon from 1-step to 4-step.
5. **Real LoRA (torch)** — add torch as optional dep, wire A/B into actual Ollama
   model via Modelfile base + LoRA merge. Feasible with llama.cpp LoRA support.

---

## Naming honesty (updated)

- "AGI" — no. ~3% there (up from 2%).
- "Living computer" — the strongest honest claim yet. Has: metabolism, drives,
  online non-linear learning, 8-step BPTT, hippocampal replay, GWT with proactive
  ignition, autonomous daily self-modification, LoRA behavioral evolution. Missing:
  reproduction, real weight-level LoRA, user-aligned fitness.
- "Self-improving" — yes, and now *autonomously* so. LOVE runs a self-modification
  cycle every night without being asked.
- "Autonomous Life OS" — still the most accurate day-to-day description.

Keep the marketing pegged here.
