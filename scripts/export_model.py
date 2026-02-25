import os
from ultralytics import YOLO

def main():
    # 1. Khởi tạo đường dẫn
    model_path = "models/yolov8n.pt"
    
    # Đảm bảo thư mục models tồn tại
    if not os.path.exists("models"):
        os.makedirs("models")

    # 2. Tải model gốc vào thư mục models/
    # Nếu file đã tồn tại, YOLO sẽ tự động load từ đó
    print(f"--- Step 1: Loading/Downloading {model_path} ---")
    model = YOLO(model_path)

    # 3. Xuất sang OpenVINO
    # YOLO sẽ tự tạo thư mục 'yolov8n_openvino_model' ngay tại vị trí file .pt
    print("--- Step 2: Exporting to OpenVINO format ---")
    model.export(format='openvino')

    print(f"\nSuccess! Model is ready in: models/yolov8n_openvino_model/")

if __name__ == "__main__":
    main()