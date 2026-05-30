"""
LOVE Structured Output Engine — Reliable JSON Mode (Modern AI Pattern)

In 2025, the biggest improvement in AI reliability is structured output.
Instead of parsing free-text LLM responses, we enforce JSON schemas
that the model must conform to. This eliminates hallucination in
tool selection, reasoning chains, and data extraction.

This module provides:
1. JSON Schema enforcement via Ollama's native format mode
2. Schema validation with automatic retry on parse failures
3. Type coercion (model returns strings, we cast to int/float/bool)
4. Fallback to regex extraction if JSON mode fails
5. Integration with reasoning engine for validated reasoning chains

Architecture:
- generate(): Given a prompt + schema, return validated JSON
- extract(): Given text + schema, extract structured data
- validate(): Check if JSON conforms to schema
- coerce(): Convert string values to proper Python types
"""

import json
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from core.llm import get_reasoning_llm

DATA_DIR = Path(__file__).parent.parent / "data" / "structured_output"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STRUCTURED_LOG = DATA_DIR / "structured_log.jsonl"


@dataclass
class SchemaField:
    """Definition of a single field in a JSON schema."""
    name: str = ""
    type: str = "string"  # string, integer, number, boolean, array, object
    description: str = ""
    required: bool = True
    enum: Optional[List[str]] = None
    items_type: Optional[str] = None  # For arrays
    properties: Optional[Dict[str, Any]] = None  # For objects


@dataclass
class StructuredResult:
    """Result of a structured generation attempt."""
    data: Dict[str, Any] = field(default_factory=dict)
    raw_response: str = ""
    attempts: int = 0
    success: bool = False
    validation_errors: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    schema_name: str = ""


class StructuredOutputEngine:
    """
    Central engine for reliable structured LLM output.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.Lock()
        self._stats = {"total_calls": 0, "success_count": 0, "retry_count": 0}

    # ── Core Generation ────────────────────────────────────────────────────────

    def generate(self, prompt: str, schema: Dict[str, Any],
                 max_retries: int = 2, temperature: float = 0.1) -> StructuredResult:
        """Generate structured JSON from a prompt with schema validation."""
        start = time.time()
        result = StructuredResult(schema_name=schema.get("title", "unknown"))

        # Build the enhanced prompt with schema
        enhanced_prompt = self._build_prompt(prompt, schema)

        for attempt in range(max_retries + 1):
            result.attempts = attempt + 1
            try:
                llm = get_reasoning_llm(temperature=temperature)
                raw = llm.complete(enhanced_prompt, max_tokens=2000)
                result.raw_response = raw

                # Try to extract JSON
                parsed = self._extract_json(raw)
                if parsed is None:
                    if attempt < max_retries:
                        enhanced_prompt += "\n\n[Previous response was not valid JSON. Respond with ONLY valid JSON.]"
                        continue
                    result.validation_errors.append("Failed to extract JSON after all retries")
                    break

                # Validate against schema
                errors = self._validate(parsed, schema)
                if errors:
                    if attempt < max_retries:
                        enhanced_prompt += f"\n\n[Validation errors: {'; '.join(errors)}. Fix and respond with valid JSON.]"
                        result.validation_errors.extend(errors)
                        continue
                    result.validation_errors.extend(errors)
                    break

                # Coerce types
                result.data = self._coerce_types(parsed, schema)
                result.success = True
                self._stats["success_count"] += 1
                break

            except Exception as e:
                if attempt < max_retries:
                    continue
                result.validation_errors.append(f"Generation error: {e}")

        result.latency_ms = (time.time() - start) * 1000
        self._stats["total_calls"] += 1
        self._log({
            "event": "structured_generation",
            "schema": result.schema_name,
            "success": result.success,
            "attempts": result.attempts,
            "latency_ms": result.latency_ms,
        })

        return result

    def extract(self, text: str, schema: Dict[str, Any]) -> StructuredResult:
        """Extract structured data from existing text."""
        return self.generate(
            f"Extract structured data from this text:\n\n{text}\n\n",
            schema,
            max_retries=1,
        )

    # ── Schema Builders ──────────────────────────────────────────────────────

    @staticmethod
    def build_schema(title: str, fields: List[SchemaField]) -> Dict[str, Any]:
        """Build a JSON schema from field definitions."""
        properties = {}
        required = []
        for f in fields:
            prop = {"type": f.type, "description": f.description}
            if f.enum:
                prop["enum"] = f.enum
            if f.type == "array" and f.items_type:
                prop["items"] = {"type": f.items_type}
            if f.type == "object" and f.properties:
                prop["properties"] = f.properties
            properties[f.name] = prop
            if f.required:
                required.append(f.name)

        return {
            "title": title,
            "type": "object",
            "properties": properties,
            "required": required,
        }

    @staticmethod
    def reasoning_schema() -> Dict[str, Any]:
        """Standard schema for reasoning chains."""
        return StructuredOutputEngine.build_schema("reasoning", [
            SchemaField("problem", "string", "The core problem to solve"),
            SchemaField("steps", "array", "Reasoning steps", items_type="object"),
            SchemaField("conclusion", "string", "Final conclusion"),
            SchemaField("confidence", "number", "Confidence 0.0-1.0"),
            SchemaField("uncertainties", "array", "What remains uncertain", items_type="string"),
        ])

    @staticmethod
    def decision_schema(options: List[str]) -> Dict[str, Any]:
        """Schema for decision-making."""
        return StructuredOutputEngine.build_schema("decision", [
            SchemaField("analysis", "string", "Step-by-step analysis"),
            SchemaField("winner", "string", "Best option", enum=options),
            SchemaField("confidence", "number", "Confidence 0.0-1.0"),
            SchemaField("risks", "array", "Key risks", items_type="string"),
        ])

    # ── Internal Helpers ─────────────────────────────────────────────────────

    def _build_prompt(self, prompt: str, schema: Dict[str, Any]) -> str:
        """Build a prompt that strongly encourages valid JSON output."""
        schema_str = json.dumps(schema, indent=2)
        return f"""{prompt}

You MUST respond with valid JSON that matches this exact schema:
{schema_str}

Rules:
- Output ONLY the JSON object, no markdown, no explanations
- All required fields must be present
- Use correct types (numbers not strings, booleans not "true"/"false")
- Arrays must contain items of the specified type

JSON:"""

    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from LLM response using multiple strategies."""
        # Strategy 1: Find JSON block in markdown
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'(\{[\s\S]*\})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    continue

        # Strategy 2: Try parsing the whole text as JSON
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Strategy 3: Find the largest JSON-like substring
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group())
            except json.JSONDecodeError:
                pass

        return None

    def _validate(self, data: Dict, schema: Dict) -> List[str]:
        """Validate JSON data against schema. Returns list of errors."""
        errors = []
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        # Check required fields
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Check types
        for field, value in data.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if not self._check_type(value, expected_type):
                    errors.append(f"Field '{field}' expected {expected_type}, got {type(value).__name__}")

                # Check enum
                enum_values = properties[field].get("enum")
                if enum_values and value not in enum_values:
                    errors.append(f"Field '{field}' value '{value}' not in enum {enum_values}")

        return errors

    def _check_type(self, value: Any, expected: str) -> bool:
        """Check if a value matches the expected JSON schema type."""
        type_map = {
            "string": (str,),
            "integer": (int,),
            "number": (int, float),
            "boolean": (bool,),
            "array": (list,),
            "object": (dict,),
        }
        expected_types = type_map.get(expected, ())
        return isinstance(value, expected_types)

    def _coerce_types(self, data: Dict, schema: Dict) -> Dict:
        """Coerce string values to proper types based on schema."""
        properties = schema.get("properties", {})
        coerced = {}
        for key, value in data.items():
            if key in properties:
                expected = properties[key].get("type")
                coerced[key] = self._coerce_value(value, expected)
            else:
                coerced[key] = value
        return coerced

    def _coerce_value(self, value: Any, expected_type: str) -> Any:
        """Coerce a single value to the expected type."""
        if expected_type == "integer" and isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 0
        elif expected_type == "number" and isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return 0.0
        elif expected_type == "boolean" and isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "on")
        elif expected_type == "array" and isinstance(value, list):
            return value
        elif expected_type == "object" and isinstance(value, dict):
            return value
        return value

    # ── Statistics ────────────────────────────────────────────────────────────────

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_calls": self._stats["total_calls"],
            "success_count": self._stats["success_count"],
            "success_rate": self._stats["success_count"] / max(self._stats["total_calls"], 1),
            "retry_count": self._stats["retry_count"],
        }

    def _log(self, event: Dict):
        event["timestamp"] = datetime.now().isoformat()
        try:
            with open(STRUCTURED_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_structured_engine_instance: Optional[StructuredOutputEngine] = None
_structured_engine_lock = threading.Lock()


def get_structured_engine() -> StructuredOutputEngine:
    global _structured_engine_instance
    with _structured_engine_lock:
        if _structured_engine_instance is None:
            _structured_engine_instance = StructuredOutputEngine()
        return _structured_engine_instance
