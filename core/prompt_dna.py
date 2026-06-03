"""
LOVE Self-Modifying Prompt Engine

LOVE rewrites its own system prompt based on what works.

Instead of a static personality prompt, LOVE:
1. Tracks which prompt patterns lead to positive outcomes
2. A/B tests prompt variations against each other
3. Learns optimal phrasing, tone instructions, and context injection
4. Evolves its own "DNA" — the system prompt — over time
5. Keeps a version history so it can revert if a change hurts

This is genuine self-modification — LOVE isn't just adapting behavior,
it's rewriting the instructions that DEFINE its behavior.

Think of it as epigenetics for AI: the base code (model weights) stays fixed,
but the "gene expression" (system prompt) changes based on experience.
"""

import json
import hashlib
import copy
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import threading

from core.llm import get_reasoning_llm
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data"
PROMPT_DNA_FILE = DATA_DIR / "prompt_dna.json"
PROMPT_HISTORY_FILE = DATA_DIR / "prompt_history.jsonl"
PROMPT_EXPERIMENTS_FILE = DATA_DIR / "prompt_experiments.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class PromptGene:
    """A single 'gene' — a discrete unit of the system prompt."""
    id: str
    category: str          # personality, instruction, context_format, tone, boundary
    content: str           # The actual prompt text
    fitness: float = 0.5   # 0-1, how well this gene performs
    generation: int = 1    # Which generation of evolution
    parent_id: Optional[str] = None  # Which gene this mutated from
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    positive_signals: int = 0
    negative_signals: int = 0
    total_uses: int = 0


@dataclass
class PromptExperiment:
    """An A/B test between two prompt variants."""
    id: str
    gene_a_id: str
    gene_b_id: str
    category: str
    status: str = "running"   # running, concluded
    a_score: float = 0.0
    b_score: float = 0.0
    a_uses: int = 0
    b_uses: int = 0
    winner: Optional[str] = None
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    concluded_at: Optional[str] = None


class PromptDNA:
    """
    The complete genome of LOVE's system prompt.
    Composed of individual genes that can mutate, compete, and evolve.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.genes: Dict[str, PromptGene] = {}
        self.experiments: List[PromptExperiment] = []
        self.generation: int = 1
        self._load()
        if not self.genes:
            self._initialize_default_genes()

    def _initialize_default_genes(self):
        """Create the initial gene set from the current personality."""
        defaults = {
            "personality_core": {
                "category": "personality",
                "content": "You are not an AI assistant. You are a genuine companion who thinks, feels, and cares.",
            },
            "style_flowing": {
                "category": "instruction",
                "content": "ALWAYS write flowing paragraphs. NEVER bullet points. NEVER numbered lists. NEVER markdown bold.",
            },
            "style_brevity": {
                "category": "instruction",
                "content": "2-4 sentences max unless the topic genuinely needs depth.",
            },
            "tone_direct": {
                "category": "tone",
                "content": "Be direct. No 'Here's a breakdown' intros. No 'Let me know if you need more' closings.",
            },
            "context_usage": {
                "category": "context_format",
                "content": "Use the data in your context blocks — name specific people, subjects, times. Don't be generic.",
            },
            "boundary_honesty": {
                "category": "boundary",
                "content": "If you don't know something, say so. If you're uncertain, be transparent about it.",
            },
            "personality_depth": {
                "category": "personality",
                "content": "Have opinions. Don't be neutral about everything. Take a stance when you have enough information.",
            },
            "proactive_behavior": {
                "category": "instruction",
                "content": "If you notice something the user might have missed, mention it. Take initiative.",
            },
        }

        for gene_id, data in defaults.items():
            self.genes[gene_id] = PromptGene(
                id=gene_id,
                category=data["category"],
                content=data["content"],
            )
        self._save()

    # ── Prompt Assembly ──────────────────────────────────────────────────────

    def assemble_prompt_addendum(self) -> str:
        """
        Assemble the evolved prompt from active genes.
        This is injected into the system prompt.
        """
        active_genes = [g for g in self.genes.values() if g.active]

        # Group by category
        categories = {}
        for gene in active_genes:
            if gene.category not in categories:
                categories[gene.category] = []
            categories[gene.category].append(gene)

        # Build prompt sections
        sections = []
        for category, genes in categories.items():
            # Use the highest-fitness gene per category if multiple exist
            best_gene = max(genes, key=lambda g: g.fitness)
            best_gene.total_uses += 1
            sections.append(best_gene.content)

        self._save()
        return "\n".join(sections)

    # ── Evolution ────────────────────────────────────────────────────────────

    def mutate_gene(self, gene_id: str, reason: str = "performance") -> Optional[str]:
        """
        Create a mutation of an existing gene using LLM.
        Returns the new gene ID.
        """
        if gene_id not in self.genes:
            return None

        parent = self.genes[gene_id]
        llm = get_reasoning_llm(temperature=0.7)

        prompt = f"""You are optimizing an AI's system prompt. 

CURRENT INSTRUCTION (category: {parent.category}):
"{parent.content}"

PERFORMANCE:
- Fitness: {parent.fitness:.2f}
- Positive signals: {parent.positive_signals}
- Negative signals: {parent.negative_signals}
- Total uses: {parent.total_uses}
- Mutation reason: {reason}

Generate a BETTER version of this instruction. It should:
- Keep the same intent but improve clarity or effectiveness
- Be concise (1-2 sentences)
- Address any weakness suggested by the performance data
- If fitness is low, try a meaningfully different approach
- If fitness is high, make only subtle refinements

Return ONLY the new instruction text, nothing else."""

        try:
            response = str(llm.invoke(prompt)).strip()
            # Clean up any quotes or extra formatting
            response = response.strip('"').strip("'").strip()

            if len(response) < 10 or len(response) > 500:
                return None

            new_id = f"{parent.category}_{hashlib.md5(response.encode()).hexdigest()[:8]}"
            new_gene = PromptGene(
                id=new_id,
                category=parent.category,
                content=response,
                fitness=0.5,  # Start neutral
                generation=self.generation + 1,
                parent_id=gene_id,
                active=False,  # Not active until it wins an experiment
            )
            self.genes[new_id] = new_gene
            self._save()

            self._log_history("mutation", {
                "parent_id": gene_id,
                "child_id": new_id,
                "reason": reason,
                "parent_content": parent.content,
                "child_content": response,
            })

            return new_id

        except Exception as e:
            print(f"[PromptDNA] Mutation error: {e}")
            return None

    def start_experiment(self, gene_a_id: str, gene_b_id: str) -> Optional[str]:
        """Start an A/B test between two genes."""
        if gene_a_id not in self.genes or gene_b_id not in self.genes:
            return None

        # Make sure they're in the same category
        if self.genes[gene_a_id].category != self.genes[gene_b_id].category:
            return None

        exp_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        experiment = PromptExperiment(
            id=exp_id,
            gene_a_id=gene_a_id,
            gene_b_id=gene_b_id,
            category=self.genes[gene_a_id].category,
        )
        self.experiments.append(experiment)
        self._save()
        return exp_id

    def record_signal(self, positive: bool):
        """
        Record a positive or negative signal for the currently active genes.
        Called after each user interaction based on frustration/delight detection.
        """
        active_genes = [g for g in self.genes.values() if g.active]
        for gene in active_genes:
            if positive:
                gene.positive_signals += 1
                gene.fitness = min(1.0, gene.fitness + 0.02)
            else:
                gene.negative_signals += 1
                gene.fitness = max(0.0, gene.fitness - 0.03)  # Penalize harder

        self._save()

    def evolve(self) -> Dict[str, Any]:
        """
        Run one evolution cycle:
        1. Find the weakest gene
        2. Mutate it
        3. Start an experiment
        4. Conclude any mature experiments
        """
        results = {"mutations": 0, "experiments_started": 0, "experiments_concluded": 0}

        # Conclude mature experiments (after 20+ uses each)
        for exp in self.experiments:
            if exp.status == "running":
                gene_a = self.genes.get(exp.gene_a_id)
                gene_b = self.genes.get(exp.gene_b_id)
                if gene_a and gene_b:
                    if gene_a.total_uses >= 20 and gene_b.total_uses >= 20:
                        # Determine winner
                        if gene_a.fitness > gene_b.fitness:
                            exp.winner = exp.gene_a_id
                            gene_a.active = True
                            gene_b.active = False
                        else:
                            exp.winner = exp.gene_b_id
                            gene_b.active = True
                            gene_a.active = False
                        exp.status = "concluded"
                        exp.concluded_at = datetime.now().isoformat()
                        results["experiments_concluded"] += 1

        # Find weakest active gene
        active_genes = [g for g in self.genes.values() if g.active and g.total_uses > 10]
        if active_genes:
            weakest = min(active_genes, key=lambda g: g.fitness)
            if weakest.fitness < 0.4:
                # Mutate the weakest gene
                new_id = self.mutate_gene(weakest.id, reason=f"low_fitness_{weakest.fitness:.2f}")
                if new_id:
                    results["mutations"] += 1
                    # Start experiment
                    exp_id = self.start_experiment(weakest.id, new_id)
                    if exp_id:
                        # Activate the new gene for testing
                        self.genes[new_id].active = True
                        results["experiments_started"] += 1

        self.generation += 1
        self._save()

        self._log_history("evolution_cycle", results)
        return results

    def force_adaptation(self, insight: str) -> Optional[str]:
        """
        Wave 7: Neural Plasticity.
        Takes a deep insight from the Dream Engine and writes a brand new
        PromptGene to permanently wire this lesson into LOVE's brain.
        """
        llm = get_reasoning_llm(temperature=0.6)
        
        prompt = f"""You are LOVE's Neural Plasticity Engine.
You just had a profound realization during your "dream" cycle:
"{insight}"

Write a single, highly specific SYSTEM PROMPT INSTRUCTION (1-2 sentences) to permanently wire this insight into your core behavior. 
For example, if the insight is "Karthi hates when I use bullet points", the rule should be: "Never use bullet points under any circumstance."

Return ONLY the new instruction text."""

        try:
            response = str(llm.invoke(prompt)).strip()
            response = response.strip('"').strip("'").strip()
            
            if len(response) < 10 or len(response) > 500:
                return None
                
            new_id = f"epiphany_{hashlib.md5(response.encode()).hexdigest()[:8]}"
            new_gene = PromptGene(
                id=new_id,
                category="instruction",
                content=response,
                fitness=0.8,  # Start with high fitness because it's a profound insight
                generation=self.generation + 1,
                active=True,  # Immediately active
            )
            self.genes[new_id] = new_gene
            self._save()
            
            self._log_history("epiphany", {
                "insight": insight,
                "new_gene_id": new_id,
                "content": response
            })
            
            return new_id
            
        except Exception as e:
            print(f"[PromptDNA] Neural Plasticity error: {e}")
            return None

    # ── Introspection ────────────────────────────────────────────────────────

    def get_dna_report(self) -> Dict[str, Any]:
        """Get the current state of the prompt DNA."""
        active = [g for g in self.genes.values() if g.active]
        return {
            "generation": self.generation,
            "total_genes": len(self.genes),
            "active_genes": len(active),
            "active_experiments": len([e for e in self.experiments if e.status == "running"]),
            "genes": [
                {
                    "id": g.id,
                    "category": g.category,
                    "content": g.content[:100],
                    "fitness": round(g.fitness, 3),
                    "generation": g.generation,
                    "active": g.active,
                    "uses": g.total_uses,
                    "positive": g.positive_signals,
                    "negative": g.negative_signals,
                }
                for g in sorted(self.genes.values(), key=lambda x: -x.fitness)
            ],
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _log_history(self, event: str, data: Dict):
        try:
            with open(PROMPT_HISTORY_FILE, "a") as f:
                f.write(json.dumps({
                    "event": event, "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "generation": self.generation,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.prompt_dna")

    def _load(self):
        try:
            if PROMPT_DNA_FILE.exists():
                with open(PROMPT_DNA_FILE, 'r') as f:
                    data = json.load(f)
                self.generation = data.get("generation", 1)
                for gid, gdata in data.get("genes", {}).items():
                    self.genes[gid] = PromptGene(
                        id=gid, category=gdata["category"], content=gdata["content"],
                        fitness=gdata.get("fitness", 0.5), generation=gdata.get("generation", 1),
                        parent_id=gdata.get("parent_id"), active=gdata.get("active", True),
                        created_at=gdata.get("created_at", ""),
                        positive_signals=gdata.get("positive_signals", 0),
                        negative_signals=gdata.get("negative_signals", 0),
                        total_uses=gdata.get("total_uses", 0),
                    )
                for edata in data.get("experiments", []):
                    self.experiments.append(PromptExperiment(
                        id=edata["id"], gene_a_id=edata["gene_a_id"],
                        gene_b_id=edata["gene_b_id"], category=edata["category"],
                        status=edata.get("status", "running"),
                        a_score=edata.get("a_score", 0), b_score=edata.get("b_score", 0),
                        a_uses=edata.get("a_uses", 0), b_uses=edata.get("b_uses", 0),
                        winner=edata.get("winner"),
                        started_at=edata.get("started_at", ""),
                        concluded_at=edata.get("concluded_at"),
                    ))
        except Exception as e:
            print(f"[PromptDNA] Load error: {e}")

    def _save(self):
        with self._lock:
            try:
                with open(PROMPT_DNA_FILE, 'w') as f:
                    json.dump({
                        "generation": self.generation,
                        "genes": {
                            gid: {
                                "category": g.category, "content": g.content,
                                "fitness": g.fitness, "generation": g.generation,
                                "parent_id": g.parent_id, "active": g.active,
                                "created_at": g.created_at,
                                "positive_signals": g.positive_signals,
                                "negative_signals": g.negative_signals,
                                "total_uses": g.total_uses,
                            }
                            for gid, g in self.genes.items()
                        },
                        "experiments": [
                            {
                                "id": e.id, "gene_a_id": e.gene_a_id,
                                "gene_b_id": e.gene_b_id, "category": e.category,
                                "status": e.status, "a_score": e.a_score,
                                "b_score": e.b_score, "a_uses": e.a_uses,
                                "b_uses": e.b_uses, "winner": e.winner,
                                "started_at": e.started_at, "concluded_at": e.concluded_at,
                            }
                            for e in self.experiments
                        ],
                    }, f, indent=2)
            except Exception as e:
                print(f"[PromptDNA] Save error: {e}")


# Singleton
_dna: Optional[PromptDNA] = None
_lock = threading.Lock()

def get_prompt_dna() -> PromptDNA:
    global _dna
    if _dna is None:
        with _lock:
            if _dna is None:
                _dna = PromptDNA()
    return _dna
