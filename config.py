import os

# Xác định thư mục gốc của dự án (Employee-Tracker/)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Central configuration class for the Employee Tracker system.
    Defines all paths, AI parameters, and server settings.
    """

    # --- 1. DIRECTORY STRUCTURE ---
    # Centralizing all data-related folders
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
    OUTPUT_FOLDER = os.path.join(DATA_DIR, 'outputs')
    REPORT_FOLDER = os.path.join(DATA_DIR, 'reports')
    
    # AI Models directory
    MODEL_DIR = os.path.join(BASE_DIR, 'models')
    
    # --- 2. FILE PATHS ---
    # Prioritizing the OpenVINO model for Intel CPU optimization
    MODEL_PATH = os.path.join(MODEL_DIR, 'yolov8n_openvino_model')
    DB_PATH = os.path.join(DATA_DIR, 'employees.db') 
    TRACKER_CONFIG = os.path.join(MODEL_DIR, 'bytetrack.yaml')

    # --- 3. AI & PERFORMANCE TUNING ---
    # These parameters directly affect the FPS and CPU results in your CV
    TARGET_FPS = 15
    SKIP_FRAMES = 5
    CONF_THRESHOLD = 0.2
    IMG_SIZE = 640
    
    # Business Logic parameter
    MIN_WORK_DURATION = 3  # Seconds to confirm "Working" status
    PATIENCE_LIMIT = 200    # Frames to wait before confirming "Left" status

    # --- 4. FLASK & SERVER SETTINGS ---
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dtu_cs_project_2026_key'
    DEBUG = False  # Set to False for production (Waitress)

# AUTOMATED DIRECTORY INITIALIZATION
# Ensures all necessary folders exist before the engine starts
REQUIRED_FOLDERS = [
    Config.UPLOAD_FOLDER, 
    Config.OUTPUT_FOLDER, 
    Config.MODEL_DIR, 
    Config.REPORT_FOLDER
]

for folder in REQUIRED_FOLDERS:
    os.makedirs(folder, exist_ok=True)