from pathlib import Path
import cv2
import numpy as np


def _pct(mask: np.ndarray) -> float:
    return round(float(np.count_nonzero(mask)) * 100.0 / mask.size, 2)


def analyze_image(path: Path) -> dict:
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError("Uploaded image could not be decoded")

    h, w = image.shape[:2]
    resized = cv2.resize(image, (min(w, 900), int(h * min(w, 900) / w))) if w > 900 else image
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    mean_bgr = resized.mean(axis=(0, 1))
    mean_hsv = hsv.mean(axis=(0, 1))
    mean_lab = lab.mean(axis=(0, 1))

    yellow = cv2.inRange(hsv, np.array([18, 55, 45]), np.array([38, 255, 255]))
    green = cv2.inRange(hsv, np.array([38, 35, 30]), np.array([90, 255, 255]))
    brown_a = cv2.inRange(hsv, np.array([5, 45, 20]), np.array([20, 255, 190]))
    dark = cv2.inRange(gray, 0, 55)

    lap = cv2.Laplacian(gray, cv2.CV_64F)
    edges = cv2.Canny(gray, 75, 150)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
    probs = hist / max(hist.sum(), 1)
    entropy = float(-np.sum(probs[probs > 0] * np.log2(probs[probs > 0])))

    brown_pct = _pct(brown_a)
    dark_pct = _pct(dark)
    edge_density = _pct(edges)
    healthy_est = round(max(0.0, 100.0 - (brown_pct * 0.85 + dark_pct * 1.2)), 2)

    return {
        "dimensions": {"width": int(w), "height": int(h)},
        "color": {
            "mean_rgb": [round(float(mean_bgr[2]), 2), round(float(mean_bgr[1]), 2), round(float(mean_bgr[0]), 2)],
            "mean_hsv": [round(float(x), 2) for x in mean_hsv],
            "mean_lab": [round(float(x), 2) for x in mean_lab],
            "yellow_pct": _pct(yellow),
            "green_pct": _pct(green),
            "brown_pct": brown_pct,
            "dark_pct": dark_pct,
        },
        "texture": {
            "laplacian_variance": round(float(lap.var()), 3),
            "entropy": round(entropy, 3),
            "edge_density_pct": edge_density,
            "roughness_index": round(min(100.0, np.std(gray) * 1.8), 2),
        },
        "defects": {
            "healthy_surface_estimate_pct": healthy_est,
            "visible_damage_estimate_pct": round(100.0 - healthy_est, 2),
            "brown_region_pct": brown_pct,
            "dark_region_pct": dark_pct,
        },
        "note": "Computer-vision measurements are experimental features, not a food-safety determination.",
    }
