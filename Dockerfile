# Stage: base runtime image
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
# so container logs appear immediately in Cloud Run and local Docker.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Cloud Run injects PORT=8080 by default; we honour that convention.
ENV PORT=8080

WORKDIR /app

# ─────────────────────────────────────────────────────────────────────────────
# Install system dependencies required by OpenCV / Ultralytics
# ─────────────────────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ─────────────────────────────────────────────────────────────────────────────
# Install Python dependencies
# Copy requirements first to leverage Docker layer caching
# ─────────────────────────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# Copy application source code
# ─────────────────────────────────────────────────────────────────────────────
COPY app/ ./app/

# ─────────────────────────────────────────────────────────────────────────────
# Pre-download the YOLOv8 model weights at build time so the container does
# not need to fetch them from the internet at startup (Cloud Run would time
# out waiting for the port to open while the download runs).
# ─────────────────────────────────────────────────────────────────────────────
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# ─────────────────────────────────────────────────────────────────────────────
# Expose the port and run the API
# Cloud Run injects PORT at runtime; default is 8080.
# ─────────────────────────────────────────────────────────────────────────────
EXPOSE 8080

# Shell form is required so $PORT is expanded at runtime.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
