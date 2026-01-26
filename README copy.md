# Employee Tracker | Real-time AI Analytics

> **An AI-powered solution for automated workstation monitoring and productivity tracking.**
> *Overcoming the Re-Identification (Re-ID) challenge through Seat-Based Spatial Logic.*

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-000000?style=for-the-badge&logo=flask)
![YOLOv8](https://img.shields.io/badge/YOLO-v8_Ultralytics-orange?style=for-the-badge)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-red?style=for-the-badge&logo=opencv)
![SQLite](https://img.shields.io/badge/SQLite-3.0+-003B57?style=for-the-badge&logo=sqlite)

## Introduction

**Employee Tracker** is a high-performance computer vision system designed to analyze office activity and workstation occupancy. Traditional AI trackers often suffer from "ID Switching" when subjects are obscured or change posture. This project solves that by implementing **Seat-Based Identification**—mapping AI detections to predefined coordinate zones to ensure 100% data consistency.

The system features a centralized Flask dashboard for real-time monitoring, session-based logging, automated workstation occupancy analysis, and HR reporting.

---

## Demo & Preview

* **Quick Demo Video:** [Link to your YouTube/Google Drive Demo]
* **System Screenshot:**
*(Note: Add your screenshot here)*

---

## Key Features

### 1. Robust Tracking Logic

* **Spatial Seat-Lock:** Identity is locked to a specific workstation zone. Even if an employee is temporarily obscured or moves out of the frame, their session remains consistent upon return.
* **Point-in-Polygon Heuristics:** Utilizes optimized geometric algorithms to detect occupancy in complex office layouts accurately.
* **H.264 Web Optimization:** Features a **Post-Processing Pipeline** using MoviePy/FFmpeg to transcode analysis results into **H.264 (libx264)**, enabling direct browser playback.

### 2. Intelligent Data Management

* **Session Isolation:** Every analysis is treated as an independent "Session," preventing data overlap and allowing for clean historical auditing.
* **Relational Logging:** Automated event capturing (Entry/Exit/Total Duration) stored in a structured SQLite database.
* **Automated Excel Reporting:** One-click export of workstation occupancy stats to `.xlsx` format, saved automatically in `data/reports/`.

### 3. Developer & Admin Tooling

* **`scripts/draw_zones.py`:** A custom utility for rapid workspace configuration via GUI.
* **Bulk Employee Import:** Support for mass-uploading employee metadata via Excel/CSV templates.

---

## Directory Structure

The project follows the **Separation of Concerns (SoC)** principle for high maintainability:

```text
├── app.py              # Central Controller & Web Routing
├── config.py           # Centralized System Configurations & Paths
├── src/                # Core Logic (AI Pipeline & Database Operations)
├── scripts/            # Admin Utilities (Zone Drawing, Pre-processing)
├── data/               # Unified Data Hub
│   ├── uploads/        # Raw input videos
│   ├── outputs/        # AI-processed videos (H.264)
│   ├── reports/        # Generated Excel reports
│   ├── samples/        # Import templates (e.g., employee_template.xlsx)
│   └── employees.db    # Relational Database
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

**2. Configure Workspace Zones**
Define your workstation coordinates before starting the analysis:

```bash
python scripts/draw_zones.py
```

* **Actions:** Left-click to select points, press `1-9` to save zones, `q` to save and exit.

**3. Launch Dashboard**

```bash
python app.py
```

Access the dashboard at `http://127.0.0.1:5000`.

---

## AI Model Setup

The system uses the **YOLOv8** model for human detection.

1. **Automatic Download:** The system will automatically download `yolov8n.pt` on the first run.
2. **Manual Download:** If required, download it [here](https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n.pt) and place it in the `models/` directory.

---

## Employee Management

To bulk-import employees:

1. **Template:** Open `data/samples/employee_template.xlsx`.
2. **Data:** Fill in the **Mã NV** (Employee ID) and **Họ Tên** (Full Name).
3. **Upload:** Use the **"Import Nhân Sự"** button on the dashboard to update the database.

---

## Roadmap

* [x] **Session Management:** Isolated data streams per video upload.
* [x] **H.264 Web Playback:** Direct browser viewing of AI results.
* [x] **Automated Reporting:** `.xlsx` export functionality for HR auditing.
* [ ] **Live RTSP Support:** Direct connection to IP Surveillance Cameras.
* [ ] **Asynchronous Processing:** Background video processing using Celery/Redis.

---

## Author

**Trần Nhật Quý** - *Computer Science Senior | Duy Tan University*

* **Portfolio:** [GitHub Profile](https://github.com/Montero52)
* **LinkedIn:** [LinkedIn](https://www.linkedin.com/in/trannhatquy)
* **Email:** [trannhatquy0@gmail.com](mailto:trannhatquy0@gmail.com)

---

*Developed for academic research and industrial application in Computer Vision.*

---