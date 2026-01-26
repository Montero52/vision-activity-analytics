import os

# Xác định thư mục gốc của dự án (Employee-Tracker/)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # 1. Thư mục DATA là trung tâm (Chứa mọi thứ liên quan đến dữ liệu)
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    
    # 2. Đưa Uploads và Outputs VÀO TRONG thư mục data
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
    OUTPUT_FOLDER = os.path.join(DATA_DIR, 'outputs')
    REPORT_FOLDER = os.path.join(DATA_DIR, 'reports')

    # 3. Thư mục Model (Có thể để riêng hoặc trong data, ở đây để riêng cho chuyên nghiệp)
    MODEL_DIR = os.path.join(BASE_DIR, 'models')
    
    # Đường dẫn file cụ thể
    MODEL_PATH = os.path.join(MODEL_DIR, 'yolov8n.pt')
    DB_PATH = os.path.join(DATA_DIR, 'employees.db') 
    
    # Cấu hình Flask
    SECRET_KEY = 'employee_tracker_project_2026'
    DEBUG = True

# TỰ ĐỘNG tạo cấu trúc thư mục phân cấp
# Khi tạo UPLOAD_FOLDER (data/uploads), thư mục data/ sẽ tự động được tạo theo
for folder in [Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER, Config.MODEL_DIR, Config.REPORT_FOLDER]:
    os.makedirs(folder, exist_ok=True)