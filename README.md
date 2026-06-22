# Gridlock

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.0-000000.svg?logo=next.js)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Gridlock is an automated traffic violation detection system. It ingests real-time video feeds or static images, processes them through a cascade computer vision pipeline, and logs categorized traffic violations into a centralized dashboard for review and enforcement.

## Architecture

The system is decoupled into an asynchronous Python backend and a React-based frontend:

1. **Inference Pipeline:** Utilizes Ultralytics YOLOv8s for primary object localization (vehicles, pedestrians) and Roboflow models for specific entity recognition. 
2. **Spatial Logic Engine:** Implements deterministic, geometry-based heuristics (IoU overlap, bounding box proximity, trajectory mapping) to identify specific violations without requiring heavy, end-to-end classification models.
3. **Optical Character Recognition (OCR):** Lazily invokes PaddleOCR tailored for Indian license plate formats strictly when a spatial violation is flagged, optimizing GPU/CPU cycles.
4. **Streaming API:** The backend serves real-time annotated frames and analytics payload over Server-Sent Events (SSE) to the frontend client.

## Core Capabilities

* **Multi-Violation Detection:** Programmatic detection of helmet non-compliance, seatbelt absence, passenger overloading (triple riding), wrong-side driving, and stationary infractions (parking/stop-line).
* **Automated Evidence Generation:** Dynamically extracts, crops, and watermarks violation frames with bounding box coordinates and confidence intervals.
* **Interactive Zone Management:** Provides a UI layer to define polygon coordinates for spatial restrictions (e.g., no-parking zones).
* **High-Throughput Processing:** The FastAPI backend utilizes async generators and thread-pools (`run_in_threadpool`) to isolate blocking OpenCV and SQLite operations from the main event loop.

## Getting Started

### Prerequisites
* Python 3.10 or higher
* Node.js 18.x or higher
* (Optional) CUDA-enabled GPU for accelerated inference

### Backend Setup

1. Navigate to the backend directory and create a virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the `backend/` directory with the required API keys (see Configuration).
4. Start the server (includes database seeding):
   ```bash
   python run.py --seed
   ```
   *The API will be available at `http://localhost:8000`.*

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies and start the development server:
   ```bash
   npm install
   npm run dev
   ```
   *The application will be available at `http://localhost:3000`.*

## Configuration

The backend relies on the following environment variables, which should be defined in `backend/.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `ROBOFLOW_API_KEY` | Authentication key for Roboflow inference endpoints. | *Required* |
| `GEMINI_API_KEY` | Authentication key for multimodal fallback reasoning. | *Required* |
| `YOLO_CONFIDENCE` | Minimum confidence threshold for YOLOv8 detections. | `0.35` |
| `YOLO_IOU` | Intersection over Union threshold for NMS. | `0.45` |

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
