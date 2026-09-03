from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from ..config import BASE_DIR

REFERENCE_INDEX = BASE_DIR / "models" / "public_reference_index.json"

DATASETS = [
    {
        "id": "fruits360",
        "name": "Fruits-360",
        "purpose": "fruit_identity",
        "supports": ["Apple", "Banana", "Orange", "Mango"],
        "repo": "fruits-360/fruits-360-100x100",
        "url": "https://github.com/fruits-360/fruits-360-100x100",
        "license": "CC BY-SA 4.0",
        "note": "Large public identity dataset. Use it for training/validating fruit recognition; do not treat benchmark accuracy as FreshFusion accuracy.",
    },
    {
        "id": "public_freshness_voc",
        "name": "Fruit freshness detection dataset",
        "purpose": "freshness_reference",
        "supports": ["Apple", "Banana", "Orange"],
        "repo": "zijianchen98/Fruit-freshness-detection-dataset",
        "url": "https://github.com/zijianchen98/Fruit-freshness-detection-dataset",
        "license": "Apache-2.0",
        "labels": [
            "fresh_apple", "normal_apple", "rotten_apple",
            "fresh_banana", "normal_banana", "rotten_banana",
            "fresh_orange", "normal_orange", "rotten_orange",
        ],
        "note": "Public labelled decay reference. Its labels are kept as published; FreshFusion does not silently rename normal/rotten into four-stage ground truth.",
    },
]


def reference_index_status() -> dict:
    if not REFERENCE_INDEX.exists():
        return {
            "ready": False,
            "path": str(REFERENCE_INDEX),
            "classes": 0,
            "samples": 0,
            "generated_at": None,
        }
    try:
        payload = json.loads(REFERENCE_INDEX.read_text(encoding="utf-8"))
        classes = payload.get("classes", {})
        return {
            "ready": True,
            "path": str(REFERENCE_INDEX),
            "classes": len(classes),
            "samples": int(sum(int(v.get("count", 0)) for v in classes.values())),
            "generated_at": payload.get("generated_at"),
            "source": payload.get("source"),
        }
    except Exception as exc:
        return {
            "ready": False,
            "path": str(REFERENCE_INDEX),
            "classes": 0,
            "samples": 0,
            "generated_at": None,
            "error": str(exc),
        }


async def dataset_registry(fruit_type: str | None = None) -> dict:
    fruit = (fruit_type or "").strip().lower()
    selected = [
        dataset for dataset in DATASETS
        if not fruit or any(item.lower() == fruit for item in dataset.get("supports", []))
    ]

    async def probe(dataset: dict) -> dict:
        row = dict(dataset)
        api = f"https://api.github.com/repos/{dataset['repo']}"
        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                response = await client.get(api, headers={"Accept": "application/vnd.github+json", "User-Agent": "FreshFusion/2.3"})
                response.raise_for_status()
                meta = response.json()
            row["online"] = True
            row["updated_at"] = meta.get("pushed_at") or meta.get("updated_at")
            row["default_branch"] = meta.get("default_branch")
            row["stars"] = meta.get("stargazers_count")
        except Exception as exc:
            row["online"] = False
            row["error"] = str(exc)
        return row

    rows = []
    for dataset in selected:
        rows.append(await probe(dataset))

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "fruit_type": fruit_type,
        "datasets": rows,
        "reference_index": reference_index_status(),
        "runtime_policy": "Online sources are checked live. Image-by-image runtime comparison uses a locally cached compact reference index so a 2.5-second camera stream is not blocked by internet latency.",
    }
