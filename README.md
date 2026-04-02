# YOLOv8 Object Detection API

A production-ready REST API that wraps **YOLOv8** (Ultralytics) and exposes it over **FastAPI**.  
Images are uploaded via HTTP, and the API returns structured JSON detections (class, confidence, bounding box).  
The service is containerised with **Docker** and deployed automatically to **Google Cloud Run** via **GitHub Actions**.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Client (curl / browser / app)               │
└────────────────────────────┬─────────────────────────────────────────┘
                             │  HTTP POST /predict  (multipart image)
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        Cloud Run (europe-west1)                      │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │  Docker Container  (python:3.10-slim)                        │   │
│   │                                                              │   │
│   │   uvicorn  →  FastAPI app  →  YOLOv8n model (in-memory)     │   │
│   │                                                              │   │
│   │   app/                                                       │   │
│   │   ├── main.py      – API routes & request handling           │   │
│   │   ├── model.py     – model singleton & inference logic       │   │
│   │   └── schemas.py   – Pydantic request/response models        │   │
│   └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                             ▲
          GitHub Actions CI/CD pipeline
          (on push to main)
          1. Build Docker image
          2. Push to Artifact Registry
          3. gcloud run deploy
```

---

## Project Structure

```
.
├── app/
│   ├── __init__.py     – package marker
│   ├── main.py         – FastAPI routes (health check + predict)
│   ├── model.py        – YOLOv8 singleton + inference helper
│   └── schemas.py      – Pydantic response models
├── .github/
│   └── workflows/
│       └── deploy.yml  – GitHub Actions CI/CD workflow
├── Dockerfile          – production Docker image (python:3.10-slim)
├── requirements.txt    – pinned Python dependencies
└── README.md
```

---

## Local Setup (Windows-friendly)

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| pip | latest |
| Docker Desktop | optional, for container testing |

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/api-ml-test.git
cd api-ml-test
```

### 2. Create and activate a virtual environment

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note:** On first run, Ultralytics will automatically download the `yolov8n.pt` weights (~6 MB) from the internet.

### 4. Start the API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Open your browser at [http://localhost:8080/docs](http://localhost:8080/docs) to explore the interactive Swagger UI.

---

## Docker Usage

### Build the image

```bash
docker build -t yolov8-api:local .
```

### Run the container

```bash
docker run --rm -p 8080:8080 yolov8-api:local
```

The API is available at [http://localhost:8080](http://localhost:8080).

---

## API Reference

### `GET /` – Health check

```bash
curl http://localhost:8080/
```

**Response**
```json
{
  "status": "ok",
  "model_loaded": true
}
```

---

### `POST /predict` – Object detection

```bash
curl -X POST http://localhost:8080/predict \
     -H "accept: application/json" \
     -F "file=@/path/to/your/image.jpg"
```

**Response**
```json
{
  "detections": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.8912,
      "bounding_box": {
        "x1": 112.4,
        "y1": 38.7,
        "x2": 456.1,
        "y2": 720.0
      }
    },
    {
      "class_id": 2,
      "class_name": "car",
      "confidence": 0.7634,
      "bounding_box": {
        "x1": 600.0,
        "y1": 310.5,
        "x2": 980.2,
        "y2": 650.8
      }
    }
  ],
  "model_name": "yolov8n.pt",
  "image_width": 1280,
  "image_height": 720
}
```

---

## CI/CD – Automated Deployment to Cloud Run

Every push to the `main` branch triggers the GitHub Actions workflow (`.github/workflows/deploy.yml`):

1. **Checkout** – pulls the latest source code
2. **Authenticate** – uses a GCP service account JSON key (`GCP_SERVICE_KEY` secret)
3. **Configure Docker** – authenticates Docker to push to Google Artifact Registry
4. **Build & Push** – builds the image and pushes it with `latest` + commit-SHA tags
5. **Deploy** – runs `gcloud run deploy` targeting Cloud Run in `europe-west1` with 2 Gi memory and public access

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `GCP_PROJECT_ID` | Your GCP project ID |
| `GCP_REGION` | GCP region (e.g. `europe-west1`) |
| `GCP_SERVICE_KEY` | Base64-encoded service account JSON key |

### Minimum GCP IAM roles for the service account

- `roles/artifactregistry.writer`
- `roles/run.admin`
- `roles/iam.serviceAccountUser`

### One-time GCP setup (run once, locally)

```bash
# Create the Artifact Registry repository
gcloud artifacts repositories create yolov8-api \
  --repository-format=docker \
  --location=europe-west1 \
  --description="YOLOv8 API Docker images"
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Model loaded at module import | Avoids re-loading weights on every request; critical for low-latency inference |
| `python:3.10-slim` base image | Smaller attack surface and faster pulls than full images |
| Pinned dependency versions | Reproducible builds across environments |
| `--allow-unauthenticated` | Simplest setup for a public demo; add Cloud IAM for production auth |
| 2 Gi Cloud Run memory | YOLOv8n requires ~300 MB; 2 Gi gives headroom for concurrent requests |

---

## License

MIT
