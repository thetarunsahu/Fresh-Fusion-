from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

from .ai import predict_image
from .reference_match import infer_fruit_identity, match_reference


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
    _x, _y, bw, bh = cv2.boundingRect(contour)
    hull = cv2.convexHull(contour)
    hull_area = max(float(cv2.contourArea(hull)), 1.0)
    return {
        "aspect_ratio": round(long / short, 3),
        "circularity": round(max(0.0, min(1.0, 4.0 * math.pi * area / (perimeter * perimeter))), 3),
        "solidity": round(max(0.0, min(1.0, area / hull_area)), 3),
        "extent": round(max(0.0, min(1.0, area / max(float(bw * bh), 1.0))), 3),
    }


def _blob_shape(color_mask: np.ndarray, region: np.ndarray) -> dict:
    selected = cv2.bitwise_and(color_mask, region)
    contours, _ = cv2.findContours(selected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return {"coverage_pct": 0.0, "aspect_ratio": 0.0, "circularity": 0.0, "solidity": 0.0}
    contour = max(contours, key=cv2.contourArea)
    area = max(float(cv2.contourArea(contour)), 1.0)
    region_area = max(float(np.count_nonzero(region)), 1.0)
    perimeter = max(float(cv2.arcLength(contour, True)), 1.0)
    rw, rh = cv2.minAreaRect(contour)[1]
    short = max(min(rw, rh), 1.0)
    long = max(rw, rh)
    hull = cv2.convexHull(contour)
    hull_area = max(float(cv2.contourArea(hull)), 1.0)
    return {
        "coverage_pct": round(area / region_area * 100.0, 2),
        "aspect_ratio": round(long / short, 3),
        "circularity": round(max(0.0, min(1.0, 4.0 * math.pi * area / (perimeter * perimeter))), 3),
        "solidity": round(max(0.0, min(1.0, area / hull_area)), 3),
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


def _largest_quad_ratio(binary: np.ndarray, frame_area: float, minimum: float = 0.07) -> float:
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    largest = 0.0
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < frame_area * minimum:
            continue
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.025 * perimeter, True)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            largest = max(largest, area / frame_area)
    return largest


def _presentation_metrics(gray: np.ndarray, hsv: np.ndarray, edges: np.ndarray, mask: np.ndarray) -> dict:
    """Flag obvious monitor/photo presentation artifacts without claiming proof.

    The score intentionally combines independent clues: large rectangular panels,
    long horizontal/vertical UI lines, bright low-saturation display regions and
    pixel/moire-like periodicity. Multi-view planar checks run separately.
    """
    h, w = gray.shape[:2]
    frame_area = max(float(h * w), 1.0)

    largest_quad = _largest_quad_ratio(edges, frame_area, 0.07)

    bright_panel = (((gray > 165) & (hsv[:, :, 1] < 72)).astype(np.uint8) * 255)
    bright_panel = cv2.morphologyEx(bright_panel, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8), iterations=2)
    bright_quad = _largest_quad_ratio(bright_panel, frame_area, 0.10)

    min_len = max(36, int(min(h, w) * 0.12))
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=52, minLineLength=min_len, maxLineGap=16)
    axis_lines = 0
    long_lines = 0
    if lines is not None:
        array = np.asarray(lines).reshape(-1, 4)
        for x1, y1, x2, y2 in array[:160]:
            dx, dy = abs(int(x2) - int(x1)), abs(int(y2) - int(y1))
            length = math.hypot(dx, dy)
            if length < min_len:
                continue
            long_lines += 1
            angle = abs(math.degrees(math.atan2(dy, max(dx, 1e-6))))
            if angle <= 9 or angle >= 81:
                axis_lines += 1
    axis_ratio = axis_lines / max(long_lines, 1)
    line_score = min(1.0, axis_lines / 10.0) * (0.50 + 0.50 * axis_ratio)

    gx = np.abs(np.diff(gray.astype(np.float32), axis=1)).mean(axis=0)
    gy = np.abs(np.diff(gray.astype(np.float32), axis=0)).mean(axis=1)
    periodicity = max(_periodicity(gx), _periodicity(gy))
    periodic_score = min(1.0, periodicity / 0.14)

    quad_score = max(0.0, min(1.0, (largest_quad - 0.10) / 0.50))
    bright_score = max(0.0, min(1.0, (bright_quad - 0.14) / 0.50))
    suspicion = max(
        quad_score * 82.0,
        bright_score * 62.0 + line_score * 27.0,
        quad_score * 48.0 + line_score * 30.0 + periodic_score * 22.0,
    )

    # Strong UI/display geometry gets a decisive floor. This catches the common
    # demo failure where the phone is pointed at a browser image on a laptop.
    if largest_quad >= 0.12 and axis_lines >= 5:
        suspicion = max(suspicion, 72.0 + min(18.0, (axis_lines - 5) * 1.5))
    if bright_quad >= 0.20 and axis_lines >= 6:
        suspicion = max(suspicion, 70.0)
    if largest_quad >= 0.34:
        suspicion = max(suspicion, 82.0)
    if periodic_score >= 0.48 and axis_lines >= 4:
        suspicion = max(suspicion, 70.0)

    return {
        "screen_suspicion_pct": round(min(100.0, suspicion), 1),
        "largest_quadrilateral_pct": round(largest_quad * 100.0, 1),
        "bright_panel_quadrilateral_pct": round(bright_quad * 100.0, 1),
        "axis_line_score_pct": round(line_score * 100.0, 1),
        "axis_line_count": int(axis_lines),
        "periodicity_score_pct": round(periodic_score * 100.0, 1),
        "fruit_fingerprint": _fruit_fingerprint(gray, mask),
        "method": "display geometry + bright panel + straight-line + periodic artifact heuristics",
        "note": "Single-frame screen/photo detection is heuristic. Final physical verification also uses changed-view planar consistency.",
    }


def _detect_identity(shape: dict, color: dict, quality: dict, blobs: dict, reference_identity: dict) -> dict:
    if not quality.get("fruit_present"):
        return {
            "fruit": "Unknown",
            "confidence": 0.0,
            "method": "visual identity gate",
            "shape": shape,
            "supported": ["Apple", "Banana"],
            "reference_identity": reference_identity,
            "blob_cues": blobs,
        }

    aspect = float(shape.get("aspect_ratio", 0.0))
    circularity = float(shape.get("circularity", 0.0))
    solidity = float(shape.get("solidity", 0.0))
    yellow = float(color.get("yellow_pct", 0.0))
    green = float(color.get("green_pct", 0.0))
    red = float(color.get("red_pct", 0.0))
    yellow_green = yellow + green

    red_blob = blobs.get("red", {})
    yg_blob = blobs.get("yellow_green", {})
    red_blob_cov = float(red_blob.get("coverage_pct", 0.0))
    red_blob_circ = float(red_blob.get("circularity", 0.0))
    red_blob_aspect = float(red_blob.get("aspect_ratio", 99.0))
    yg_blob_cov = float(yg_blob.get("coverage_pct", 0.0))
    yg_blob_circ = float(yg_blob.get("circularity", 0.0))
    yg_blob_aspect = float(yg_blob.get("aspect_ratio", 0.0))

    strong_apple = red_blob_cov >= 13.0 and red_blob_circ >= 0.42 and red_blob_aspect <= 1.70
    strong_banana = yg_blob_cov >= 18.0 and yg_blob_aspect >= 1.45 and yg_blob_circ <= 0.72 and red_blob_cov < 14.0

    if strong_apple and not strong_banana:
        confidence = min(96.0, 80.0 + min(10.0, red_blob_cov * 0.18) + min(6.0, red_blob_circ * 6.0))
        fruit = "Apple"
        method = "dominant red rounded-blob cue"
        scores = {"apple": 1.0, "banana": 0.0}
    elif strong_banana and not strong_apple:
        confidence = min(96.0, 79.0 + min(11.0, yg_blob_cov * 0.16) + min(6.0, max(0.0, yg_blob_aspect - 1.3) * 5.0))
        fruit = "Banana"
        method = "elongated yellow/green-blob cue"
        scores = {"apple": 0.0, "banana": 1.0}
    else:
        banana_score = 0.0
        apple_score = 0.0
        banana_score += min(1.0, max(0.0, (aspect - 1.28) / 1.15)) * 0.48
        banana_score += min(1.0, max(0.0, (0.70 - circularity) / 0.36)) * 0.16
        banana_score += min(1.0, yellow_green / 52.0) * 0.25
        banana_score += min(1.0, yg_blob_cov / 35.0) * 0.11

        apple_score += min(1.0, max(0.0, (1.58 - aspect) / 0.72)) * 0.34
        apple_score += min(1.0, max(0.0, (circularity - 0.42) / 0.46)) * 0.20
        apple_score += min(1.0, red / 38.0) * 0.28
        apple_score += min(1.0, red_blob_cov / 28.0) * 0.13
        apple_score += min(1.0, solidity) * 0.05

        total = banana_score + apple_score
        if total <= 0.15:
            fruit, confidence = "Unknown", 0.0
        elif banana_score >= apple_score:
            fruit, confidence = "Banana", banana_score / max(total, 1e-6)
        else:
            fruit, confidence = "Apple", apple_score / max(total, 1e-6)

        separation = abs(banana_score - apple_score)
        confidence = min(0.94, max(0.0, confidence * (0.72 + min(0.28, separation)))) * 100.0
        method = "shape+color+blob controlled-chamber fallback"
        scores = {"apple": round(apple_score, 3), "banana": round(banana_score, 3)}

        ref_fruit = str(reference_identity.get("fruit") or "Unknown")
        ref_conf = float(reference_identity.get("confidence") or 0.0)
        ref_margin = float(reference_identity.get("margin") or 0.0)
        if ref_fruit in {"Apple", "Banana"}:
            if ref_fruit == fruit:
                confidence = min(96.0, max(confidence, confidence * 0.68 + ref_conf * 0.32))
                method += "+public-reference agreement"
            elif ref_conf >= 64.0 and ref_margin >= 5.0 and confidence < 80.0:
                fruit = ref_fruit
                confidence = min(92.0, ref_conf)
                method = "public-reference override of ambiguous visual fallback"

        if confidence < 58.0:
            fruit = "Unknown"

    return {
        "fruit": fruit,
        "confidence": round(float(confidence), 1),
        "method": method,
        "shape": shape,
        "scores": scores,
        "supported": ["Apple", "Banana"],
        "blob_cues": blobs,
        "reference_identity": reference_identity,
        "note": "Identity combines fruit-shape/color blobs with the cached public reference index. It is still a prototype fallback until the trained identity model is deployed.",
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
        cv2.inRange(hsv, np.array([0, 55, 40]), np.array([10, 255, 255])),
        cv2.inRange(hsv, np.array([168, 55, 40]), np.array([179, 255, 255])),
    )
    brown = cv2.inRange(hsv, np.array([5, 42, 18]), np.array([20, 255, 190]))
    dark = cv2.inRange(gray, 0, 55)

    lap = cv2.Laplacian(gray, cv2.CV_64F)
    edges = cv2.Canny(gray, 75, 150)
    presentation = _presentation_metrics(gray, hsv, edges, mask)
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

    blobs = {
        "red": _blob_shape(red, mask) if fruit_present else {},
        "yellow_green": _blob_shape(cv2.bitwise_or(yellow, green), mask) if fruit_present else {},
    }
    preliminary = {
        "quality": quality,
        "color": color,
        "texture": {
            "roughness_index": roughness,
            "edge_density_pct": edge_density,
            "entropy": round(entropy, 3) if fruit_present else 0.0,
        },
        "identity": {"shape": shape},
    }
    reference_identity = infer_fruit_identity(preliminary)
    identity = _detect_identity(shape, color, quality, blobs, reference_identity)

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
