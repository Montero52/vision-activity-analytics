# Vision Activity Analytics | Real-time & Batch AI Pipeline

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![OpenVINO](https://img.shields.io/badge/Intel-OpenVINO-orange.svg)](https://docs.openvino.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![YOLOv8](https://img.shields.io/badge/Model-YOLOv8-success.svg)](https://ultralytics.com/)
[![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey.svg)](https://flask.palletsprojects.com/)

An industrial-grade computer vision solution for automated workstation occupancy analytics and productivity auditing, optimized for Intel hardware.

<div align="center">
  <img src="assets/images/demo.gif" width="750" alt="Vision Activity Analytics Demo">
  <p><i>Real-time Employee Monitoring & Spatial Activity Analytics Optimized by OpenVINO™</i></p>
</div>

---
## Project Overview
Vision Activity Analytics (VAA) transforms raw surveillance footage into actionable behavioral insights. The system effectively mitigates **Re-Identification (Re-ID)** challenges common in traditional trackers by implementing **Seat-Based Spatial Logic**. Engineered for edge computing, it leverages OpenVINO to ensure high-throughput execution on commodity Intel CPUs.

## Performance Benchmarks (Intel® Optimized)
*Environment: Tested on Intel Core i-series (OpenVINO Integrated)*

| Metric | Live AI (Streaming) | Batch Processing (Offline) | Status |
| :--- | :--- | :--- | :--- |
| **Inference Latency** | 71.24 ms | 60.88 ms | Sustained |
| **Throughput** | 13.6 FPS | 19.0 FPS | Near Real-time |
| **CPU Utilization** | 56.7 % | 78.4 % | High Efficiency |

> **Technical Insight:** Leveraging JIT (Just-In-Time) compilation and model warming, cold-start latency was reduced from 501.33ms to 66.63ms (an **86% improvement**).

## Key Technical Highlights
### 1. Robust Spatial Logic & Tracking
* **Spatial Seat-Locking:** Instead of relying on volatile visual descriptors, the system anchors identities to static polygonal workstation coordinates.
* **Anchor Point Heuristics:** Utilizes an optimized anchor at 25% of the bounding box height for `pointPolygonTest` operations, bypassing desk-level occlusions.
* **Anti-Merging Filters:** Implements dual-criteria filtering (Area > 22,000px & Aspect Ratio > 0.7) to prevent "box-merging" in crowded office perspectives.

### 2. Production-Grade Pipeline
* **Dual-Mode Architecture:** Features bandwidth-optimized **Live Preview** and throughput-optimized **Turbo Batch Export**.
* **H.264 Web Transcoding:** Automated pipeline using FFmpeg to transcode results for native, cross-browser HTML5 playback.
* **Industrial Deployment:** Powered by **Waitress WSGI** to ensure robust concurrency and production-level stability.

## Tech Stack
* **Core:** YOLOv8, OpenVINO™ Toolkit.
* **Backend:** Python, Flask, Waitress WSGI.
* **Processing:** OpenCV, NumPy, Pandas, MoviePy.
* **Storage:** SQLite (Event Logging) & Excel (Automated HR Reporting).

## Project Structure
```text
vision-activity-analytics/
├── assets/images/       # Project demonstrations (GIFs/Images)
├── data/                # Local database, zones config, and samples
├── models/              # AI weights (YOLO, OpenVINO)
├── scripts/             # Utility scripts (Export, Draw Zones, Setup)
├── src/                 # Core logic (Inference, Database, Camera)
├── static/              # Frontend assets (CSS, JS)
├── templates/           # Web UI templates (HTML)
├── app.py               # Main entry point
├── config.py            # Global system configurations
├── requirements.txt     # Project dependencies
└── run_system.bat       # Windows automation script (Setup & Launch)
```

## One-Click Launch (Windows Optimized)
For the most convenient experience on Windows, a dedicated automation script is provided. This script manages the virtual environment, installs dependencies, and warms up the AI engine automatically.

1. **Run the Script:** Double-click `run_system.bat` from the root directory.
2. **Automated Process:**
* **Environment Check:** Automatically creates a `.venv` if it doesn't exist.
* **Dependency Sync:** Installs/updates required libraries quietly.
* **OpenVINO Warming:** Prepares the AI Engine for optimal inference.
* **Auto-Launch:** Automatically opens the Dashboard in your default browser at `http://127.0.0.1:5000`.

> **Note:** Please allow 15-20 seconds for the AI Engine to initialize during the first run.

## Quick Start

### 1. Prerequisites

* **Python 3.9+**
* **FFmpeg** installed on system path
* **Intel CPU** (Recommended for OpenVINO™ hardware acceleration)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/Montero52/vision-activity-analytics.git
cd vision-activity-analytics

# Setup Virtual Environment
python -m venv .venv
source .venv/bin/activate # Windows: .venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
```

### 3. Model Setup (Automated)

Instead of downloading heavy weights manually, run the following script to download the YOLOv8n model and export it to the optimized **OpenVINO™** format:

```bash
python scripts/export_model.py
```

*This script will generate the optimized model files in the `models/yolov8n_openvino_model/` directory.*

### 4. Configuration & Launch

```bash
# Define your monitoring zones (Polygonal)
python scripts/draw_zones.py

# Launch the Dashboard
python app.py
```

## License
This project is licensed under the **MIT License**. It is free to use for academic and personal purposes. See the [LICENSE](LICENSE) file for the full license text.

## Author

**Trần Nhật Quý** *Computer Science Student | Duy Tan University* | [LinkedIn](https://www.linkedin.com/in/trannhatquy) | [GitHub](https://github.com/Montero52)  | [Email](mailto:trannhatquy0@gmail.com)