"""FreshFusion service compatibility helpers.

OpenCV's Python wheels have returned ``HoughLinesP`` data in both ``(N, 1, 4)``
and ``(N, 4)`` shapes across platforms/builds. FreshFusion's presentation-artifact
analysis expects the nested form. Normalize it once at package import time so
Windows and Linux behave consistently and a camera frame can never fail merely
because of that ABI shape difference.
"""

import cv2
import numpy as np

_original_hough_lines_p = cv2.HoughLinesP


def _freshfusion_hough_lines_p(*args, **kwargs):
    lines = _original_hough_lines_p(*args, **kwargs)
    if lines is None:
        return None

    array = np.asarray(lines)
    if array.ndim == 1 and array.size == 4:
        return array.reshape(1, 1, 4)
    if array.ndim == 2 and array.shape[-1] == 4:
        return array.reshape(-1, 1, 4)
    return lines


if getattr(cv2.HoughLinesP, "__name__", "") != "_freshfusion_hough_lines_p":
    cv2.HoughLinesP = _freshfusion_hough_lines_p
