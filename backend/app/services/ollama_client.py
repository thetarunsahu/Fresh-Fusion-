"""Local Ollama/Gemma client for FreshFusion.

FreshFusion's verdict remains deterministic and evidence-gated. Ollama/Gemma is
optional and may only explain, summarize, or answer questions from supplied
evidence. It must never manufacture sensor values, validation metrics, food-
safety claims, or freshness decisions.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx


class OllamaClient:
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

    async def _generate_json(self, prompt: str) -> dict[str, Any]:
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
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"answer": raw.strip()}

    async def explain(self, evidence: dict[str, Any]) -> dict[str, Any]:
        system_prompt = (
            "You are the FreshFusion evidence explainer. Use ONLY the supplied "
            "evidence. Never invent sensor values, calibration, accuracy, dataset "
            "probabilities, shelf life, or food-safety claims. If evidence is "
            "insufficient, say so. Return JSON with keys: summary, "
            "supporting_evidence, contradictions, missing_evidence, "
            "recommended_next_step."
        )
        result = await self._generate_json(
            f"{system_prompt}\n\nFRESHFUSION EVIDENCE JSON:\n"
            f"{json.dumps(evidence, ensure_ascii=False, default=str)}"
        )
        return {
            "summary": str(result.get("summary") or result.get("answer") or "Evidence explanation unavailable."),
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

    async def answer(self, question: str, evidence: dict[str, Any]) -> dict[str, Any]:
        """Answer an operator question without changing the deterministic verdict."""
        system_prompt = (
            "You are the FreshFusion inspection assistant. Answer the user's "
            "question using ONLY the supplied FreshFusion evidence and previous "
            "inspection context. Use simple operator-friendly language. Never "
            "invent values, universal MQ135 standards, accuracy, probabilities, "
            "shelf-life days, internal quality, or food-safety claims. Never "
            "override the deterministic verdict. If evidence cannot answer the "
            "question, clearly say what is missing. Return valid JSON with keys: "
            "answer, evidence_used, uncertainty, next_action."
        )
        result = await self._generate_json(
            f"{system_prompt}\n\nUSER QUESTION:\n{question}\n\n"
            "FRESHFUSION EVIDENCE JSON:\n"
            f"{json.dumps(evidence, ensure_ascii=False, default=str)}"
        )
        return {
            "answer": str(result.get("answer") or "I could not answer that from the available evidence."),
            "evidence_used": [str(x) for x in list(result.get("evidence_used") or [])[:8]],
            "uncertainty": str(result.get("uncertainty") or "Evidence limits still apply."),
            "next_action": str(result.get("next_action") or "Review the current inspection evidence."),
            "model": self.model,
            "role": "evidence_qna_only",
        }


ollama_client = OllamaClient()
