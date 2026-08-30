from pathlib import Path
import cv2
import numpy as np
from .ai import predict_image


def _pct(mask: np.ndarray, region: np.ndarray | None = None) -> float:
    if region is None:
        return round(float(np.count_nonzero(mask)) * 100.0 / mask.size, 2)
    total = max(int(np.count_nonzero(region)), 1)
    return round(float(np.count_nonzero(cv2.bitwise_and(mask, region))) * 100.0 / total, 2)


def _fruit_mask(image: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    candidate = ((sat > 32) & (val > 25)).astype(np.uint8) * 255
    kernel = np.ones((9, 9), np.uint8)
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_CLOSE, kernel, iterations=2)
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_OPEN, kernel, iterations=1)
    contours, _ = cv2.findContours(candidate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return np.ones(image.shape[:2], dtype=np.uint8) * 255
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < image.shape[0] * image.shape[1] * 0.04:
        return np.ones(image.shape[:2], dtype=np.uint8) * 255
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, [largest], -1, 255, thickness=-1)
    return mask


def _issue(label: str, severity: str, value: float, note: str) -> dict:
    return {"label": label, "severity": severity, "value": round(float(value), 2), "note": note}


def analyze_image(path: Path, fruit_type: str = "Fruit") -> dict:
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError("Uploaded image could not be decoded")

    fruit = (fruit_type or "fruit").strip().lower()
    h, w = image.shape[:2]
    scale = min(1.0, 1000.0 / w)
    resized = cv2.resize(image, (int(w * scale), int(h * scale))) if scale < 1 else image.copy()
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    mask = _fruit_mask(resized)

    pixels = resized[mask > 0]
    hsv_pixels = hsv[mask > 0]
    lab_pixels = lab[mask > 0]
    mean_bgr = pixels.mean(axis=0) if len(pixels) else resized.mean(axis=(0, 1))
    mean_hsv = hsv_pixels.mean(axis=0) if len(hsv_pixels) else hsv.mean(axis=(0, 1))
    mean_lab = lab_pixels.mean(axis=0) if len(lab_pixels) else lab.mean(axis=(0, 1))

    yellow = cv2.inRange(hsv, np.array([18, 55, 45]), np.array([38, 255, 255]))
    green = cv2.inRange(hsv, np.array([38, 35, 30]), np.array([90, 255, 255]))
    red1 = cv2.inRange(hsv, np.array([0, 55, 40]), np.array([7, 255, 255]))
    red2 = cv2.inRange(hsv, np.array([170, 55, 40]), np.array([179, 255, 255]))
    red = cv2.bitwise_or(red1, red2)
    brown = cv2.inRange(hsv, np.array([5, 42, 18]), np.array([20, 255, 190]))
    dark = cv2.inRange(gray, 0, 55)

    lap = cv2.Laplacian(gray, cv2.CV_64F)
    edges = cv2.Canny(gray, 75, 150)
    masked_gray = gray[mask > 0]
    hist, _ = np.histogram(masked_gray if len(masked_gray) else gray.ravel(), bins=256, range=(0, 256))
    probs = hist / max(hist.sum(), 1)
    entropy = float(-np.sum(probs[probs > 0] * np.log2(probs[probs > 0])))

    yellow_pct = _pct(yellow, mask)
    green_pct = _pct(green, mask)
    red_pct = _pct(red, mask)
    brown_pct = _pct(brown, mask)
    dark_pct = _pct(dark, mask)
    edge_density = _pct(edges, mask)
    roughness = round(min(100.0, float(np.std(masked_gray)) * 1.8 if len(masked_gray) else np.std(gray) * 1.8), 2)
    healthy_est = round(max(0.0, 100.0 - (brown_pct * .85 + dark_pct * 1.25)), 2)

    issues = []
    if brown_pct >= 6:
        issues.append(_issue("Brown surface regions", "high" if brown_pct >= 18 else "medium", brown_pct, "Possible bruising, senescence or surface decay; verify with additional views."))
    if dark_pct >= 2.5:
        issues.append(_issue("Dark spots", "high" if dark_pct >= 8 else "medium", dark_pct, "Dark areas may indicate bruising, shadow or decay. Review the defect overlay."))
    if roughness >= 58:
        issues.append(_issue("Surface roughness", "medium", roughness, "Texture variation is elevated compared with a smooth surface."))
    if edge_density >= 12:
        issues.append(_issue("High surface detail", "low", edge_density, "High edge density can come from wrinkles, spots, texture or lighting."))

    if fruit == "banana":
        if green_pct >= 28:
            issues.append(_issue("Strong green coverage", "info", green_pct, "This is more consistent with an earlier ripening stage than spoilage."))
        profile = "banana"
    elif fruit == "apple":
        if red_pct + green_pct + yellow_pct < 28 and brown_pct > 4:
            issues.append(_issue("Color loss / discoloration", "medium", brown_pct, "Apple skin has relatively little healthy red, green or yellow coverage in this frame."))
        profile = "apple"
    else:
        profile = "generic"

    stem = path.stem
    mask_name = f"{stem}_mask.png"
    overlay_name = f"{stem}_defects.jpg"
    edge_name = f"{stem}_edges.png"
    texture_name = f"{stem}_texture.jpg"
    cv2.imwrite(str(path.parent / mask_name), mask)

    overlay = resized.copy()
    defect_mask = cv2.bitwise_or(brown, dark)
    defect_mask = cv2.bitwise_and(defect_mask, mask)
    tint = np.zeros_like(overlay)
    tint[:, :] = (28, 42, 225)
    overlay[defect_mask > 0] = cv2.addWeighted(overlay, .42, tint, .58, 0)[defect_mask > 0]
    cv2.imwrite(str(path.parent / overlay_name), overlay)
    cv2.imwrite(str(path.parent / edge_name), cv2.bitwise_and(edges, mask))

    texture_raw = cv2.convertScaleAbs(lap)
    texture_heat = cv2.applyColorMap(texture_raw, cv2.COLORMAP_TURBO)
    texture_heat[mask == 0] = 0
    cv2.imwrite(str(path.parent / texture_name), texture_heat)

    return {
        "profile": profile,
        "fruit_type": fruit_type,
        "dimensions": {"width": int(w), "height": int(h)},
        "segmentation": {"coverage_pct": _pct(mask), "method": "largest saturated foreground region"},
        "color": {
            "mean_rgb": [round(float(mean_bgr[2]), 2), round(float(mean_bgr[1]), 2), round(float(mean_bgr[0]), 2)],
            "mean_hsv": [round(float(x), 2) for x in mean_hsv],
            "mean_lab": [round(float(x), 2) for x in mean_lab],
            "red_pct": red_pct,
            "yellow_pct": yellow_pct,
            "green_pct": green_pct,
            "brown_pct": brown_pct,
            "dark_pct": dark_pct,
        },
        "texture": {
            "laplacian_variance": round(float(lap[mask > 0].var()) if np.any(mask > 0) else float(lap.var()), 3),
            "entropy": round(entropy, 3),
            "edge_density_pct": edge_density,
            "roughness_index": roughness,
        },
        "defects": {
            "healthy_surface_estimate_pct": healthy_est,
            "visible_damage_estimate_pct": round(100.0 - healthy_est, 2),
            "brown_region_pct": brown_pct,
            "dark_region_pct": dark_pct,
        },
        "issues": issues,
        "artifacts": {
            "mask": mask_name,
            "defect_overlay": overlay_name,
            "edges": edge_name,
            "texture": texture_name,
        },
        "ai": predict_image(path),
        "note": "Image observations are experimental prototype measurements. Lighting, angle and background can affect them; they are not a food-safety determination."
    }
