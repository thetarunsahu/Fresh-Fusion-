"""Local Ollama/Gemma client for FreshFusion.

FreshFusion's core verdict remains independent of Ollama. Gemma may explain or
answer questions about already-computed evidence, but it cannot unlock, replace,
or invent the deterministic assessment.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx


class OllamaClient:
    """Small async client for a local Ollama server."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 45.0,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("FRESHFUSION_OLLAMA_URL")
            or "http://127.0.0.1:11434"
        ).rstrip("/")
        self.model = model or os.getenv("FRESHFUSION_OLLAMA_MODEL") or "gemma3:4b"
        self.timeout_seconds = timeout_seconds

    async def health(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            return {
                "available": False,
                "model": self.model,
                "base_url": self.base_url,
                "error": str(exc),
            }

        models = [
            item.get("name")
            for item in payload.get("models", [])
            if isinstance(item, dict) and item.get("name")
        ]
        return {
            "available": True,
            "model": self.model,
            "model_installed": self.model in models,
            "installed_models": models,
            "base_url": self.base_url,
        }

    async def explain(
        self,
        evidence: dict[str, Any],
        question: str | None = None,
    ) -> dict[str, Any]:
        """Explain supplied evidence or answer one evidence-grounded question."""
        system_prompt = (
            "You are the FreshFusion evidence explainer. Use ONLY the supplied "
            "FreshFusion evidence. Never invent sensor values, calibration, accuracy, "
            "dataset probabilities, food-safety claims, or a freshness verdict that "
            "is not present in the deterministic decision. If evidence is missing or "
            "contradictory, state that clearly. The deterministic critic/fusion result "
            "is authoritative. Return valid JSON with keys: summary, "
            "supporting_evidence, contradictions, missing_evidence, "
            "recommended_next_step."
        )
        user_question = (question or "").strip()
        question_block = (
            f"\n\nUSER QUESTION:\n{user_question}"
            if user_question
            else "\n\nTASK:\nExplain the current evidence and what should happen next."
        )
        prompt = (
            f"{system_prompt}"
            f"{question_block}\n\n"
            "FRESHFUSION EVIDENCE JSON:\n"
            f"{json.dumps(evidence, ensure_ascii=False, default=str)}"
        )

        request_payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=request_payload,
            )
            response.raise_for_status()
            payload = response.json()

        raw = payload.get("response", "{}")
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = {
                "summary": raw.strip() or "No explanation returned.",
                "supporting_evidence": [],
                "contradictions": [],
                "missing_evidence": [],
                "recommended_next_step": "Review deterministic FreshFusion evidence.",
            }

        return {
            "summary": str(result.get("summary") or "Evidence explanation unavailable."),
            "supporting_evidence": list(result.get("supporting_evidence") or []),
            "contradictions": list(result.get("contradictions") or []),
            "missing_evidence": list(result.get("missing_evidence") or []),
            "recommended_next_step": str(
                result.get("recommended_next_step")
                or "Review deterministic FreshFusion evidence."
            ),
            "question": user_question or None,
            "model": self.model,
            "role": "explanation_only",
        }


ollama_client = OllamaClient()
