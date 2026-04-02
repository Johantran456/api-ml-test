"""
schemas.py
----------
Pydantic models that define the shape of our API request/response payloads.
Using Pydantic ensures automatic data validation and clean OpenAPI documentation.
"""

from typing import List
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Pixel coordinates of a detected object (top-left → bottom-right)."""

    x1: float = Field(..., description="Left edge of the bounding box")
    y1: float = Field(..., description="Top edge of the bounding box")
    x2: float = Field(..., description="Right edge of the bounding box")
    y2: float = Field(..., description="Bottom edge of the bounding box")


class Detection(BaseModel):
    """A single object detection result returned by the model."""

    class_id: int = Field(..., description="Numeric class index from the YOLO model")
    class_name: str = Field(..., description="Human-readable label (e.g. 'person')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence in [0, 1]")
    bounding_box: BoundingBox = Field(..., description="Pixel-space bounding box")


class PredictResponse(BaseModel):
    """Full response payload from POST /predict."""

    detections: List[Detection] = Field(
        ..., description="List of all objects detected in the uploaded image"
    )
    model_name: str = Field(..., description="Identifier of the YOLO model used")
    image_width: int = Field(..., description="Width of the input image in pixels")
    image_height: int = Field(..., description="Height of the input image in pixels")


class HealthResponse(BaseModel):
    """Response payload from GET /."""

    status: str = Field(default="ok")
    model_loaded: bool = Field(..., description="True when the YOLO model is ready")
