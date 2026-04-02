"""
model.py
--------
Responsible for loading the YOLOv8 model exactly once at application startup.

Loading the model here (module level) ensures it is shared across all
incoming requests without reloading it on every call – a critical
performance optimisation for production inference services.
"""

import logging
from typing import List

from ultralytics import YOLO

from app.schemas import BoundingBox, Detection

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
# YOLOv8n (nano) is used as the default; swap the weight name for a larger
# variant (yolov8s, yolov8m, yolov8l, yolov8x) when you need better accuracy.
MODEL_NAME = "yolov8n.pt"

# ---------------------------------------------------------------------------
# Singleton – loaded once at import time
# ---------------------------------------------------------------------------
logger.info("Loading YOLO model '%s' …", MODEL_NAME)
_model = YOLO(MODEL_NAME)
logger.info("YOLO model loaded successfully.")


def is_model_loaded() -> bool:
    """Return True if the model singleton is available."""
    return _model is not None


def run_inference(image, confidence_threshold: float = 0.25) -> List[Detection]:
    """
    Run YOLOv8 inference on a PIL Image and return structured detections.

    Parameters
    ----------
    image:
        A PIL.Image instance (RGB or RGBA – converted internally).
    confidence_threshold:
        Minimum confidence score to include a detection.

    Returns
    -------
    List[Detection]
        One ``Detection`` object per detected bounding box.
    """
    # Ultralytics accepts PIL Images directly; it handles RGB conversion.
    results = _model.predict(source=image, conf=confidence_threshold, verbose=False)

    detections: List[Detection] = []

    for result in results:
        boxes = result.boxes  # Boxes object with .xyxy, .cls, .conf

        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = _model.names[class_id]

            detections.append(
                Detection(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=round(confidence, 4),
                    bounding_box=BoundingBox(
                        x1=round(x1, 2),
                        y1=round(y1, 2),
                        x2=round(x2, 2),
                        y2=round(y2, 2),
                    ),
                )
            )

    logger.info("Inference complete – %d detection(s) found.", len(detections))
    return detections
