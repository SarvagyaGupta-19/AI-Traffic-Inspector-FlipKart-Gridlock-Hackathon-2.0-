# 🚦 GRIDLOCK: Automated Photo Identification and Classification for Traffic Violations

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.0-000000.svg?logo=next.js)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Project Name:** GRIDLOCK - The Ultimate AI Traffic Inspector  
**Hackathon:** Flipkart Gridlock Hackathon 2.0  
**Team/Submitter:** Sarvagya Gupta

---

## 📖 Overview: The Solution Framework

With the increasing deployment of traffic surveillance cameras and automated monitoring systems, large volumes of traffic images are generated every day. Manual inspection of these images to identify traffic violations is labor-intensive, time-consuming, and prone to inconsistencies. 

**Gridlock** is a unique, practical, and highly innovative computer vision solution that directly addresses this real-world problem. Serving as a complete **Solution Framework & Prototype**, Gridlock automatically processes traffic images and live video streams to detect vehicles and road users, identify and classify multiple traffic violations, and generate pristine annotated evidence for law enforcement review.

Our system is designed to be highly robust to varying environmental conditions and traffic densities, ensuring maximum accuracy and horizontal scalability.

---

## 🎯 How We Addressed the Hackathon Tasks

We mapped our engineering directly to the core challenges outlined in the problem statement. Here is how Gridlock executes each required task:

### 1. Image Preprocessing
Gridlock enhances image quality and normalizes inputs before passing them to the AI pipeline. 
* **Dynamic Adjustment:** We utilize OpenCV techniques (like CLAHE for contrast enhancement and Otsu's thresholding) to handle challenges such as low light, heavy shadows, and rain.
* **Motion Blur Handling:** Frames with excessive motion blur are smoothed and sharpened to preserve license plate fidelity.

### 2. Vehicle and Road User Detection
* **High-Speed Localization:** We deploy **YOLOv8s** for blazing-fast inference, localizing bounding boxes for vehicles, riders, drivers, and pedestrians.
* **Classification:** The model categorizes road users into distinct groups (`car`, `motorcycle`, `person`, `bus`, `truck`) ensuring accurate context for violation logic.

### 3. Traffic Violation Detection & Classification
Gridlock doesn't rely on slow, monolithic classifiers. Instead, it utilizes a highly explainable **Spatial Logic Engine** to identify and categorize violations with assigned confidence scores:

| Violation Type | Detection Logic |
| :--- | :--- |
| **Helmet non-compliance** | Calculates proximity between `person` and `motorcycle` IoUs, then analyzes the head region using HSV skin-tone masking. |
| **Seatbelt non-compliance** | Extracts the driver's torso region and uses Canny edge detection + Hough line transforms to find diagonal belt bands. |
| **Triple riding** | Person clustering overlap on motorcycles. Flags if 3+ bounding boxes intersect heavily on a single two-wheeler. |
| **Wrong-side driving** | Dynamic trajectory analysis over user-defined polygon zones. |
| **Stop-line violation** | Ray-casting point-in-polygon logic crossing interactive intersection boundaries. |
| **Red-light violation** | Zonal analysis coupled with traffic-light state tracking. |
| **Illegal parking** | Stationary vehicle detection mapped to restricted geo-fenced zones. |

### 4. License Plate Recognition
* **Efficient OCR:** Lazily invokes **PaddleOCR** (optimized for Indian license plates) *only* when a spatial violation is flagged. This saves massive computational overhead.
* **Regex Validation:** Extracts registration details and cleans OCR hallucinations using Indian RTO format regex (e.g., `KA 01 AB 1234`).
* **Multimodal Fallback:** Gemini Vision models are leveraged as a fallback for severely degraded plates.

### 5. Evidence Generation
* **Tamper-Proof Annotations:** Dynamically crops and watermarks violation frames with bright bounding boxes, corner markers, and confidence intervals.
* **Metadata Storage:** Automatically stores timestamps, locations, plate strings, and violation types into a fast, thread-safe SQLite database.

### 6. Analytics and Reporting
* **Interactive Dashboard:** Built with Next.js 15, the frontend offers a cinematic UI for officers to review violations.
* **Insights:** Generates violation statistics, day-by-day trend graphs, and searchable records. Officers can mark challans as "Pending", "Issued", or "Rejected".

### 7. Performance Evaluation & Scalability
* **Efficiency First:** The FastAPI backend utilizes async generators and thread-pools (`run_in_threadpool`) to isolate blocking OpenCV operations from the main event loop.
* **Metrics Tracked:** The pipeline monitors processing latency, bounding box precision, and OCR confidence levels per frame, ensuring a scalable throughput for multiple camera feeds.

---

## 🚀 Expected Outcome Achieved

Gridlock successfully delivers a **scalable AI-based traffic image analysis system**. It automatically identifies, classifies, and documents traffic violations from photographic evidence, drastically reducing manual enforcement effort while establishing a modern, tamper-proof system for municipal monitoring.

---

## 🛠️ Getting Started

### Prerequisites
* Python 3.10+
* Node.js 18.x+
* (Optional) CUDA-enabled GPU for accelerated inference

### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
*Configure your `.env` file with necessary keys before running:*
```bash
python run.py --seed
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Open `http://localhost:3000` to access the Gridlock Officer Dashboard.*

---
*Built for the Flipkart Gridlock Hackathon 2.0*
