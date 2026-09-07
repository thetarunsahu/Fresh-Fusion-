"""Local Ollama/Gemma client for FreshFusion.

This module is intentionally optional: FreshFusion's core verdict must continue to
work from CV, sensor evidence, reference matching, physical validation, and the
deterministic fusion/critic path even when Ollama is unavailable.

Gemma is used only for evidence-grounded explanations and summaries. It is not
allowed to invent freshness scores, calibrated gas values, or validation metrics.
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
        """Return availability without making Ollama a hard dependency."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:  # Ollama is optional by design.
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

    async def explain(self, evidence: dict[str, Any]) -> dict[str, Any]:
        """Create a structured, evidence-grounded explanation with Gemma.

        The caller should pass already-computed evidence. Gemma may summarize and
        point out contradictions/missing evidence, but it must not manufacture a
        final numeric freshness score.
        """
        system_prompt = (
            "You are the FreshFusion evidence explainer. Use ONLY the supplied "
            "evidence. Never invent sensor values, calibration, accuracy, dataset "
            "probabilities, or food-safety claims. If evidence is insufficient, "
            "say so. Return valid JSON with keys: summary, supporting_evidence, "
            "contradictions, missing_evidence, recommended_next_step."
        )
        prompt = (
            f"{system_prompt}\n\n"
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

        # Normalize the contract so the frontend never depends on arbitrary LLM keys.
        return {
            "summary": str(result.get("summary") or "Evidence explanation unavailable."),
            "supporting_evidence": list(result.get("supporting_evidence") or []),
            "contradictions": list(result.get("contradictions") or []),
            "missing_evidence": list(result.get("missing_evidence") or []),
            "recommended_next_step": str(
                result.get("recommended_next_step")
                or "Review deterministic FreshFusion evidence."
            ),
            "model": self.model,
            "role": "explanation_only",
        }


ollama_client = OllamaClient()
