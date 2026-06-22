FROM python:3.11-slim

# Install system dependencies for OpenCV and PaddleOCR
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Create output directories
RUN mkdir -p output/uploads output/evidence weights data/samples

# Download YOLOv8s model weights on build
RUN python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"

# Expose port
EXPOSE 8000

# Run with demo data seeded
CMD ["python", "run.py", "--seed", "--host", "0.0.0.0", "--port", "8000"]
