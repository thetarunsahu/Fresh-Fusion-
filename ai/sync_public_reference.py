from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / ".datasets" / "public_freshness"
INDEX_PATH = ROOT / "models" / "public_reference_index.json"
REPO_URL = "https://github.com/zijianchen98/Fruit-freshness-detection-dataset.git"
SUPPORTED = {
    "fresh_apple": ("Apple", "fresh"),
    "normal_apple": ("Apple", "normal"),
    "rotten_apple": ("Apple", "rotten"),
    "fresh_banana": ("Banana", "fresh"),
    "normal_banana": ("Banana", "normal"),
    "rotten_banana": ("Banana", "rotten"),
    "fresh_orange": ("Orange", "fresh"),
    "normal_orange": ("Orange", "normal"),
    "rotten_orange": ("Orange", "rotten"),
}


def pct(mask: np.ndarray, region: np.ndarray) -> float:
    total = max(int(np.count_nonzero(region)), 1)
    return float(np.count_nonzero(cv2.bitwise_and(mask, region))) / total


def fruit_mask(image: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    candidate = ((sat > 30) & (val > 25)).astype(np.uint8) * 255
    kernel = np.ones((7, 7), np.uint8)
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_CLOSE, kernel, iterations=2)
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_OPEN, kernel, iterations=1)
    contours, _ = cv2.findContours(candidate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return np.ones(image.shape[:2], dtype=np.uint8) * 255
    largest = max(contours, key=cv2.contourArea)
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, [largest], -1, 255, -1)
    return mask


def vector_for(path: Path) -> list[float] | None:
    image = cv2.imread(str(path))
    if image is None:
        return None
    h, w = image.shape[:2]
    scale = min(1.0, 700.0 / max(w, 1))
    if scale < 1.0:
        image = cv2.resize(image, (max(1, int(w * scale)), max(1, int(h * scale))))
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = fruit_mask(image)

    yellow = cv2.inRange(hsv, np.array([18, 55, 45]), np.array([38, 255, 255]))
    green = cv2.inRange(hsv, np.array([38, 35, 30]), np.array([90, 255, 255]))
    red = cv2.bitwise_or(
        cv2.inRange(hsv, np.array([0, 55, 40]), np.array([7, 255, 255])),
        cv2.inRange(hsv, np.array([170, 55, 40]), np.array([179, 255, 255])),
    )
    brown = cv2.inRange(hsv, np.array([5, 42, 18]), np.array([20, 255, 190]))
    dark = cv2.inRange(gray, 0, 55)
    edges = cv2.Canny(gray, 75, 150)
    masked_gray = gray[mask > 0]
    roughness = min(1.0, (float(np.std(masked_gray)) * 1.8 if len(masked_gray) else float(np.std(gray)) * 1.8) / 100.0)
    edge_density = min(1.0, pct(edges, mask))
    hist, _ = np.histogram(masked_gray if len(masked_gray) else gray.ravel(), bins=256, range=(0, 256))
    probabilities = hist / max(hist.sum(), 1)
    entropy = float(-np.sum(probabilities[probabilities > 0] * np.log2(probabilities[probabilities > 0]))) / 8.0

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        contour = max(contours, key=cv2.contourArea)
        area = max(cv2.contourArea(contour), 1.0)
        perimeter = max(cv2.arcLength(contour, True), 1.0)
        rect = cv2.minAreaRect(contour)[1]
        short = max(min(rect), 1.0)
        long = max(rect)
        aspect = min(2.0, (long / short) / 3.0)
        circularity = max(0.0, min(1.0, 4.0 * math.pi * area / (perimeter * perimeter)))
    else:
        aspect, circularity = 1.0 / 3.0, 0.0

    return [
        pct(red, mask),
        pct(yellow, mask),
        pct(green, mask),
        pct(brown, mask),
        pct(dark, mask),
        roughness,
        edge_density,
        min(1.5, entropy),
        aspect,
        circularity,
    ]


def ensure_dataset(refresh: bool) -> None:
    if refresh and DATA_ROOT.exists():
        shutil.rmtree(DATA_ROOT)
    if DATA_ROOT.exists() and (DATA_ROOT / "Annotations").exists():
        return
    DATA_ROOT.parent.mkdir(parents=True, exist_ok=True)
    print(f"Cloning public reference dataset into {DATA_ROOT} ...")
    subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(DATA_ROOT)], check=True)


def build_index(max_per_class: int) -> dict:
    grouped: dict[str, list[list[float]]] = defaultdict(list)
    annotations = sorted((DATA_ROOT / "Annotations").glob("*.xml"))
    for index, xml_path in enumerate(annotations, start=1):
        try:
            root = ET.parse(xml_path).getroot()
            name = (root.findtext("object/name") or "").strip().lower()
            filename = (root.findtext("filename") or "").strip()
        except Exception:
            continue
        if name not in SUPPORTED or len(grouped[name]) >= max_per_class:
            continue
        image_path = DATA_ROOT / "JPEGImages" / filename
        values = vector_for(image_path)
        if values is not None:
            grouped[name].append(values)
        if index % 250 == 0:
            counts = ", ".join(f"{key}:{len(value)}" for key, value in sorted(grouped.items()))
            print(f"Scanned {index}/{len(annotations)} annotations — {counts}")
        if all(len(grouped[label]) >= max_per_class for label in SUPPORTED):
            break

    classes = {}
    for label, values in grouped.items():
        if not values:
            continue
        matrix = np.asarray(values, dtype=np.float64)
        fruit, stage = SUPPORTED[label]
        classes[label] = {
            "fruit": fruit,
            "stage": stage,
            "count": int(matrix.shape[0]),
            "mean": [round(float(v), 6) for v in matrix.mean(axis=0)],
            "std": [round(max(0.04, float(v)), 6) for v in matrix.std(axis=0)],
        }

    return {
        "source": {
            "name": "Fruit freshness detection dataset",
            "repo": "zijianchen98/Fruit-freshness-detection-dataset",
            "url": "https://github.com/zijianchen98/Fruit-freshness-detection-dataset",
            "license": "Apache-2.0",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feature_names": [
            "red", "yellow", "green", "brown", "dark", "roughness",
            "edge_density", "entropy", "aspect_ratio", "circularity",
        ],
        "classes": classes,
        "note": "Compact reference statistics from published labels. These are reference similarities, not validated FreshFusion ground truth or model accuracy.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync a public fruit freshness dataset and build a compact reference index.")
    parser.add_argument("--max-per-class", type=int, default=180, help="Maximum images used per published class")
    parser.add_argument("--refresh", action="store_true", help="Re-clone the public dataset before indexing")
    args = parser.parse_args()

    ensure_dataset(args.refresh)
    payload = build_index(max(20, args.max_per_class))
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    total = sum(row["count"] for row in payload["classes"].values())
    print(f"Reference index ready: {INDEX_PATH}")
    print(f"Classes: {len(payload['classes'])}; reference images: {total}")
    if len(payload["classes"]) < 6:
        print("Warning: fewer expected Apple/Banana classes were indexed. Inspect dataset clone/network state.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"Dataset sync failed: {exc}", file=sys.stderr)
        raise SystemExit(exc.returncode)
