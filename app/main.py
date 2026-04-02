"""
main.py
-------
FastAPI application entry-point.

Endpoints
---------
GET  /         – health check
POST /predict  – image upload → object detections (JSON)
"""

import io
import logging
import logging.config

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image

from app import model as yolo_model
from app.schemas import HealthResponse, PredictResponse

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
# Configure once at startup so every module inherits a consistent format.
logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["console"]},
    }
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="YOLOv8 Object Detection API",
    description=(
        "Production-ready REST API that wraps a YOLOv8 model. "
        "Upload an image to the /predict endpoint and receive JSON detections."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_model=HealthResponse, summary="Health check")
def health_check() -> HealthResponse:
    """
    Return the service status and whether the model is loaded.

    This endpoint is polled by Cloud Run's health probe and load balancers.
    """
    return HealthResponse(
        status="ok",
        model_loaded=yolo_model.is_model_loaded(),
    )


@app.post("/predict", response_model=PredictResponse, summary="Run object detection")
async def predict(file: UploadFile = File(..., description="Image file to analyze")) -> PredictResponse:
    """
    Accept an image upload and return all detected objects.

    The image is decoded in-memory (no disk I/O) and passed directly to the
    YOLOv8 model. Supported formats: JPEG, PNG, BMP, WEBP.
    """

    # -----------------------------------------------------------------------
    # 1. Validate content type
    # -----------------------------------------------------------------------
    if file.content_type not in ("image/jpeg", "image/png", "image/bmp", "image/webp"):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type '{file.content_type}'. "
                   "Please upload a JPEG, PNG, BMP, or WEBP image.",
        )

    # -----------------------------------------------------------------------
    # 2. Read & decode the image
    # -----------------------------------------------------------------------
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as exc:
        logger.exception("Failed to decode uploaded image: %s", exc)
        raise HTTPException(status_code=400, detail="Could not decode the uploaded image.") from exc

    width, height = image.size
    logger.info("Image received – size: %dx%d, content-type: %s", width, height, file.content_type)

    # -----------------------------------------------------------------------
    # 3. Run inference
    # -----------------------------------------------------------------------
    detections = yolo_model.run_inference(image)

    return PredictResponse(
        detections=detections,
        model_name=yolo_model.MODEL_NAME,
        image_width=width,
        image_height=height,
    )
