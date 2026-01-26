# Employee Tracker | Real-time AI Analytics

> **An AI-powered solution for automated workstation monitoring and productivity tracking.** > *Overcoming the Re-Identification (Re-ID) challenge through Seat-Based Spatial Logic.*

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-000000?style=for-the-badge&logo=flask)
![YOLOv8](https://img.shields.io/badge/YOLO-v8_Ultralytics-orange?style=for-the-badge)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-red?style=for-the-badge&logo=opencv)
![SQLite](https://img.shields.io/badge/SQLite-3.0+-003B57?style=for-the-badge&logo=sqlite)

## Introduction

**Employee Tracker** is a high-performance computer vision system designed to analyze office activity and workstation occupancy. Traditional AI trackers often suffer from "ID Switching" when subjects are obscured or change posture. This project solves that by implementing **Seat-Based Identification**—mapping AI detections to predefined coordinate zones to ensure 100% data consistency.

The system features a centralized Flask dashboard for real-time monitoring, session-based logging, and automated HR reporting.

---
<!-- ## Demo & Preview
Can't run the code right now? Check out the system in action:

* **Quick Demo Video:** [Link YouTube/Google Drive của bạn]
* **Project Screenshots:** ![Dashboard Preview](static/assets/previews/dashboard.png)
--- -->

## Key Features

### 1. Robust Tracking Logic

* **Spatial Seat-Lock:** Instead of relying solely on visual IDs, the system locks identity to a specific workstation zone. This ensures that even if an employee is temporarily obscured, their work session remains uninterrupted.
* **Point-in-Polygon Heuristics:** Utilizes optimized geometric algorithms to detect occupancy in complex office layouts.
* **H.264 Web Optimization:** Includes a dedicated **Post-Processing Pipeline** using MoviePy/FFmpeg to transcode analysis results into **H.264 (libx264)**. This allows high-quality playback directly in modern web browsers without external codecs.

### 2. Intelligent Data Management

* **Session Isolation:** Every analysis is treated as an independent "Session," preventing data overlap and allowing for clean historical auditing.
* **Relational Logging:** Automated event capturing (Entry/Exit/Total Duration) stored in a structured SQLite database.
* **Automated Excel Reporting:** One-click export of employee performance and occupancy stats to `.xlsx` format.

### 3. Developer Tooling

* **`scripts/draw_zones.py`:** A custom-built utility for rapid workspace configuration.
* **Configuration-Centric Design:** Centralized `config.py` for easy environment setup and data directory management.

---

## Directory Structure

The project follows the **Separation of Concerns (SoC)** principle:

```text
├── app.py              # Central Controller & Web Routing
├── config.py           # Centralized System Configurations & Paths
├── src/                # Core Logic (AI Pipeline & Database Operations)
├── scripts/            # Admin Utilities (Zone Drawing, Pre-processing)
├── data/               # Unified Data Hub (Uploads, Outputs, DB, JSON)
├── models/             # AI Model weights (YOLOv8) & Tracker configs
├── static/             # Frontend Assets (CSS, JS, Web Fonts)
└── templates/          # Jinja2 Dashboard Templates
```

---

## Tech Stack

| Component | Technology | Role |
| --- | --- | --- |
| **Backend** | Python 3.9+ | Core AI pipeline and server logic. |
| **Web Framework** | Flask | Real-time dashboard and I/O handling. |
| **Computer Vision** | OpenCV | Image manipulation and geometric analysis. |
| **Video Encoding** | MoviePy (FFmpeg) | Web-optimized H.264 transcoding. |
| **AI Model** | YOLOv8 + ByteTrack | Object detection and centroid tracking. |
| **Database** | SQLite & Pandas | Persistent logging and report generation. |
---

## Installation & Deployment

**1. Clone & Environment Setup**

```bash
git clone https://github.com/Montero52/employee-tracker.git
cd employee-tracker

python -m venv venv
# Windows: venv\Scripts\activate | Linux: source venv/bin/activate

pip install -r requirements.txt
```

**2. Configure Surveillance Zones**
Define your workstation coordinates before starting the analysis:

```bash
python scripts/draw_zones.py
```

* **Actions:** Left-click to select points, press `1-9` to save zones, `q` to exit.

**3. Run the Dashboard**

```bash
python app.py
```

Access the dashboard at `http://127.0.0.1:5000`.

---
### AI Model Setup
The system uses the **YOLOv8** model for human detection. Due to file size limits, the weight file is not included in this repository.

1. **Automatic Download:** The system will automatically download the `yolov8n.pt` model upon first execution.
2. **Manual Download:** If you have network issues, download it [here](https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n.pt) and place it in the `models/` directory.
---

## Roadmap

* [x] **Session Management:** Isolated data streams per video upload.
* [x] **H.264 Web Playback:** Direct browser viewing of AI results.
* [x] **Automated Reporting:** `.xlsx` export functionality for HR auditing.
* [ ] **RTSP Integration:** Direct connection to IP Surveillance Cameras.
* [ ] **Asynchronous Processing:** Integration with Celery/Redis for background tasking.

---

## Author

**Trần Nhật Quý** *Computer Science | Duy Tan University*

* **Project Portfolio:** [GitHub Profile](https://github.com/Montero52)
* **LinkedIn:** [LinkedIn](https://www.linkedin.com/in/trannhatquy)
* **Email:** [trannhatquy0@gmail.com](mailto:trannhatquy0@gmail.com)

---

*Developed for academic research and industrial application in Computer Vision.*

---

