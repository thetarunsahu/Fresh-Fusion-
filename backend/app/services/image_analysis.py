from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

from .ai import predict_image
from .reference_match import match_reference


def _pct(mask: np.ndarray, region: np.ndarray | None = None) -> float:
    if region is None:
        return round(float(np.count_nonzero(mask)) * 100.0 / max(mask.size, 1), 2)
    total = max(int(np.count_nonzero(region)), 1)
    return round(float(np.count_nonzero(cv2.bitwise_and(mask, region))) * 100.0 / total, 2)


def _fruit_mask(image: np.ndarray) -> tuple[np.ndarray, dict]:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    candidate = ((sat > 32) & (val > 25)).astype(np.uint8) * 255
    kernel = np.ones((9, 9), np.uint8)
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_CLOSE, kernel, iterations=2)
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_OPEN, kernel, iterations=1)
    contours, _ = cv2.findContours(candidate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = image.shape[:2]
    frame_area = max(float(h * w), 1.0)
    center = np.array([w / 2.0, h / 2.0])
    max_center_distance = math.hypot(w / 2.0, h / 2.0)

    ranked = []
    for contour in contours:
        area = cv2.contourArea(contour)
        coverage = area / frame_area
        if coverage < 0.025 or coverage > 0.82:
            continue
        moments = cv2.moments(contour)
        if moments["m00"]:
            centroid = np.array([moments["m10"] / moments["m00"], moments["m01"] / moments["m00"]])
        else:
            x, y, cw, ch = cv2.boundingRect(contour)
            centroid = np.array([x + cw / 2.0, y + ch / 2.0])
        center_distance = float(np.linalg.norm(centroid - center) / max(max_center_distance, 1.0))
        center_bonus = max(0.12, 1.0 - center_distance)
        score = area * center_bonus * center_bonus
        ranked.append((score, contour, coverage, center_distance))

    if not ranked:
        return np.zeros(image.shape[:2], dtype=np.uint8), {
            "coverage_pct": 0.0,
            "center_offset": 1.0,
            "method": "center-weighted saturated foreground",
        }

    _, contour, coverage, center_distance = max(ranked, key=lambda item: item[0])
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, thickness=-1)
    return mask, {
        "coverage_pct": round(coverage * 100.0, 2),
        "center_offset": round(center_distance, 3),
        "method": "center-weighted saturated foreground",
    }


def _shape(mask: np.ndarray) -> dict:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return {"aspect_ratio": 0.0, "circularity": 0.0, "solidity": 0.0, "extent": 0.0}
    contour = max(contours, key=cv2.contourArea)
    area = max(float(cv2.contourArea(contour)), 1.0)
    perimeter = max(float(cv2.arcLength(contour, True)), 1.0)
    rect_w, rect_h = cv2.minAreaRect(contour)[1]
    short = max(min(rect_w, rect_h), 1.0)
    long = max(rect_w, rect_h)
    x, y, bw, bh = cv2.boundingRect(contour)
    hull = cv2.convexHull(contour)
    hull_area = max(float(cv2.contourArea(hull)), 1.0)
    return {
        "aspect_ratio": round(long / short, 3),
        "circularity": round(max(0.0, min(1.0, 4.0 * math.pi * area / (perimeter * perimeter))), 3),
        "solidity": round(max(0.0, min(1.0, area / hull_area)), 3),
        "extent": round(max(0.0, min(1.0, area / max(float(bw * bh), 1.0))), 3),
    }


def _fruit_fingerprint(gray: np.ndarray, mask: np.ndarray) -> str | None:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
    if w < 8 or h < 8:
        return None
    crop = gray[y:y + h, x:x + w].copy()
    crop_mask = mask[y:y + h, x:x + w]
    if np.any(crop_mask > 0):
        fill = int(np.median(crop[crop_mask > 0]))
        crop[crop_mask == 0] = fill
    small = cv2.resize(crop, (9, 8), interpolation=cv2.INTER_AREA)
    diff = small[:, 1:] > small[:, :-1]
    value = 0
    for bit in diff.flatten():
        value = (value << 1) | int(bool(bit))
    return f"{value:016x}"


def _periodicity(profile: np.ndarray) -> float:
    if profile.size < 16:
        return 0.0
    values = profile.astype(np.float64)
    values -= values.mean()
    spectrum = np.abs(np.fft.rfft(values))[1:]
    total = float(spectrum.sum())
    if total <= 1e-9:
        return 0.0
    return float(np.max(spectrum) / total)


def _presentation_metrics(gray: np.ndarray, edges: np.ndarray, mask: np.ndarray) -> dict:
    """Heuristics for obvious monitor/photo presentation artifacts.

    These do not prove liveness. They are combined later with multi-view change.
    """
    h, w = gray.shape[:2]
    frame_area = max(float(h * w), 1.0)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    largest_quad = 0.0
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < frame_area * 0.12:
            continue
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.025 * perimeter, True)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            largest_quad = max(largest_quad, area / frame_area)

    min_len = max(40, int(min(h, w) * 0.18))
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=70, minLineLength=min_len, maxLineGap=12)
    axis_lines = 0
    long_lines = 0
    if lines is not None:
        for row in lines[:120]:
            x1, y1, x2, y2 = row[0]
            dx, dy = abs(x2 - x1), abs(y2 - y1)
            length = math.hypot(dx, dy)
            if length < min_len:
                continue
            long_lines += 1
            angle = abs(math.degrees(math.atan2(dy, max(dx, 1e-6))))
            if angle <= 8 or angle >= 82:
                axis_lines += 1
    axis_ratio = axis_lines / max(long_lines, 1)
    line_score = min(1.0, axis_lines / 12.0) * (0.55 + 0.45 * axis_ratio)

    gx = np.abs(np.diff(gray.astype(np.float32), axis=1)).mean(axis=0)
    gy = np.abs(np.diff(gray.astype(np.float32), axis=0)).mean(axis=1)
    periodicity = max(_periodicity(gx), _periodicity(gy))
    periodic_score = min(1.0, periodicity / 0.16)

    quad_score = max(0.0, min(1.0, (largest_quad - 0.18) / 0.55))
    suspicion = max(quad_score * 78.0, quad_score * 55.0 + line_score * 25.0 + periodic_score * 20.0)

    return {
        "screen_suspicion_pct": round(min(100.0, suspicion), 1),
        "largest_quadrilateral_pct": round(largest_quad * 100.0, 1),
        "axis_line_score_pct": round(line_score * 100.0, 1),
        "periodicity_score_pct": round(periodic_score * 100.0, 1),
        "fruit_fingerprint": _fruit_fingerprint(gray, mask),
        "method": "large-quadrilateral + straight-line + periodic-display artifact heuristics",
        "note": "Single-frame screen/photo detection is heuristic. Final physical verification also requires multiple changed viewpoints.",
    }


def _detect_identity(shape: dict, color: dict, quality: dict) -> dict:
    if not quality.get("fruit_present"):
        return {
            "fruit": "Unknown",
            "confidence": 0.0,
            "method": "shape+color controlled-chamber fallback",
            "shape": shape,
            "supported": ["Apple", "Banana"],
        }

    aspect = float(shape.get("aspect_ratio", 0.0))
    circularity = float(shape.get("circularity", 0.0))
    solidity = float(shape.get("solidity", 0.0))
    yellow_green = float(color.get("yellow_pct", 0.0)) + float(color.get("green_pct", 0.0))
    red = float(color.get("red_pct", 0.0))

    banana_score = 0.0
    apple_score = 0.0
    banana_score += min(1.0, max(0.0, (aspect - 1.25) / 1.05)) * 0.62
    banana_score += min(1.0, max(0.0, (0.72 - circularity) / 0.35)) * 0.20
    banana_score += min(1.0, yellow_green / 55.0) * 0.18
    apple_score += min(1.0, max(0.0, (1.48 - aspect) / 0.58)) * 0.52
    apple_score += min(1.0, max(0.0, (circularity - 0.48) / 0.42)) * 0.28
    apple_score += min(1.0, max(red / 45.0, solidity)) * 0.20

    total = banana_score + apple_score
    if total <= 0.15:
        fruit, confidence = "Unknown", 0.0
    elif banana_score >= apple_score:
        fruit, confidence = "Banana", banana_score / max(total, 1e-6)
    else:
        fruit, confidence = "Apple", apple_score / max(total, 1e-6)

    separation = abs(banana_score - apple_score)
    confidence = min(0.96, max(0.0, confidence * (0.72 + min(0.28, separation))))
    if confidence < 0.58:
        fruit = "Unknown"

    return {
        "fruit": fruit,
        "confidence": round(confidence * 100.0, 1),
        "method": "shape+color controlled-chamber fallback",
        "shape": shape,
        "scores": {"apple": round(apple_score, 3), "banana": round(banana_score, 3)},
        "supported": ["Apple", "Banana"],
        "note": "This fallback is designed for Apple/Banana in the centered scan chamber. Replace/augment it with a trained fruit-identity model for broader fruit support.",
    }


def _issue(label: str, severity: str, value: float, note: str) -> dict:
    return {"label": label, "severity": severity, "value": round(float(value), 2), "note": note}


def analyze_image(path: Path, fruit_type: str = "Auto") -> dict:
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError("Uploaded image could not be decoded")

    requested_fruit = (fruit_type or "Auto").strip()
    h, w = image.shape[:2]
    scale = min(1.0, 1000.0 / max(w, 1))
    resized = cv2.resize(image, (int(w * scale), int(h * scale))) if scale < 1 else image.copy()
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    mask, segmentation = _fruit_mask(resized)
    shape = _shape(mask)

    coverage = float(segmentation.get("coverage_pct", 0.0))
    center_offset = float(segmentation.get("center_offset", 1.0))
    fruit_present = bool(5.0 <= coverage <= 78.0 and center_offset <= 0.58 and np.count_nonzero(mask) > 0)

    pixels = resized[mask > 0] if np.any(mask > 0) else np.empty((0, 3), dtype=np.uint8)
    hsv_pixels = hsv[mask > 0] if np.any(mask > 0) else np.empty((0, 3), dtype=np.uint8)
    lab_pixels = lab[mask > 0] if np.any(mask > 0) else np.empty((0, 3), dtype=np.uint8)
    mean_bgr = pixels.mean(axis=0) if len(pixels) else resized.mean(axis=(0, 1))
    mean_hsv = hsv_pixels.mean(axis=0) if len(hsv_pixels) else hsv.mean(axis=(0, 1))
    mean_lab = lab_pixels.mean(axis=0) if len(lab_pixels) else lab.mean(axis=(0, 1))

    yellow = cv2.inRange(hsv, np.array([18, 55, 45]), np.array([38, 255, 255]))
    green = cv2.inRange(hsv, np.array([38, 35, 30]), np.array([90, 255, 255]))
    red = cv2.bitwise_or(
        cv2.inRange(hsv, np.array([0, 55, 40]), np.array([7, 255, 255])),
        cv2.inRange(hsv, np.array([170, 55, 40]), np.array([179, 255, 255])),
    )
    brown = cv2.inRange(hsv, np.array([5, 42, 18]), np.array([20, 255, 190]))
    dark = cv2.inRange(gray, 0, 55)

    lap = cv2.Laplacian(gray, cv2.CV_64F)
    edges = cv2.Canny(gray, 75, 150)
    presentation = _presentation_metrics(gray, edges, mask)
    masked_gray = gray[mask > 0]
    hist, _ = np.histogram(masked_gray if len(masked_gray) else gray.ravel(), bins=256, range=(0, 256))
    probs = hist / max(hist.sum(), 1)
    entropy = float(-np.sum(probs[probs > 0] * np.log2(probs[probs > 0])))

    yellow_pct = _pct(yellow, mask) if fruit_present else 0.0
    green_pct = _pct(green, mask) if fruit_present else 0.0
    red_pct = _pct(red, mask) if fruit_present else 0.0
    brown_pct = _pct(brown, mask) if fruit_present else 0.0
    dark_pct = _pct(dark, mask) if fruit_present else 0.0
    edge_density = _pct(edges, mask) if fruit_present else 0.0
    roughness = round(min(100.0, float(np.std(masked_gray)) * 1.8 if len(masked_gray) else 0.0), 2)
    healthy_est = round(max(0.0, 100.0 - (brown_pct * .85 + dark_pct * 1.25)), 2) if fruit_present else 0.0

    color = {
        "mean_rgb": [round(float(mean_bgr[2]), 2), round(float(mean_bgr[1]), 2), round(float(mean_bgr[0]), 2)],
        "mean_hsv": [round(float(x), 2) for x in mean_hsv],
        "mean_lab": [round(float(x), 2) for x in mean_lab],
        "red_pct": red_pct,
        "yellow_pct": yellow_pct,
        "green_pct": green_pct,
        "brown_pct": brown_pct,
        "dark_pct": dark_pct,
    }
    quality = {
        "fruit_present": fruit_present,
        "coverage_pct": coverage,
        "center_offset": center_offset,
        "status": "usable" if fruit_present else "no_centered_fruit",
        "message": "Fruit-like region detected inside the scan area; physical-object verification still requires multiple viewpoints." if fruit_present else "No reliable centered fruit detected. Keep the fruit inside the phone guide before trusting freshness output.",
    }
    identity = _detect_identity(shape, color, quality)

    detected = identity.get("fruit", "Unknown")
    if detected != "Unknown" and float(identity.get("confidence", 0.0)) >= 58.0:
        profile_fruit = detected
    elif requested_fruit.lower() not in {"auto", "fruit", "unknown"}:
        profile_fruit = requested_fruit.title()
    else:
        profile_fruit = "Unknown"

    issues = []
    if fruit_present:
        if brown_pct >= 6:
            issues.append(_issue("Brown surface regions", "high" if brown_pct >= 18 else "medium", brown_pct, "Possible bruising, senescence or surface decay; verify with additional views."))
        if dark_pct >= 2.5:
            issues.append(_issue("Dark spots", "high" if dark_pct >= 8 else "medium", dark_pct, "Dark areas may indicate bruising, shadow or decay. Review the defect overlay."))
        if roughness >= 58:
            issues.append(_issue("Surface roughness", "medium", roughness, "Texture variation is elevated compared with a smooth surface."))
        if edge_density >= 12:
            issues.append(_issue("High surface detail", "low", edge_density, "High edge density can come from wrinkles, spots, texture or lighting."))
        if profile_fruit.lower() == "banana" and green_pct >= 28:
            issues.append(_issue("Strong green coverage", "info", green_pct, "This is more consistent with an earlier banana ripening stage than spoilage."))
        elif profile_fruit.lower() == "apple" and red_pct + green_pct + yellow_pct < 28 and brown_pct > 4:
            issues.append(_issue("Color loss / discoloration", "medium", brown_pct, "Apple skin has relatively little healthy red, green or yellow coverage in this frame."))

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

    result = {
        "profile": profile_fruit.lower(),
        "requested_fruit_type": requested_fruit,
        "fruit_type": profile_fruit,
        "identity": identity,
        "quality": quality,
        "presentation": presentation,
        "dimensions": {"width": int(w), "height": int(h)},
        "segmentation": segmentation,
        "color": color,
        "texture": {
            "laplacian_variance": round(float(lap[mask > 0].var()) if fruit_present and np.any(mask > 0) else 0.0, 3),
            "entropy": round(entropy, 3) if fruit_present else 0.0,
            "edge_density_pct": edge_density,
            "roughness_index": roughness,
        },
        "defects": {
            "healthy_surface_estimate_pct": healthy_est,
            "visible_damage_estimate_pct": round(100.0 - healthy_est, 2) if fruit_present else 0.0,
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
        "ai": predict_image(path) if fruit_present else {"status": "no_fruit", "prediction": None, "confidence": None, "probabilities": {}},
        "note": "Image observations are experimental prototype measurements. Lighting, angle and background can affect them; they are not a food-safety determination.",
    }
    result["reference_match"] = match_reference(result, profile_fruit)
    return result
