import cv2
import json
import numpy as np
import os
import sys

# --- BIEN TOAN CUC ---
zones = {}
points = []

# Xac dinh thu muc goc cua du an (di len 1 cap tu scripts/ hoac data/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR) 

def click_event(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"Diem: ({x}, {y})")

def get_paths():
    """
    Tu dong tim duong dan video va JSON dua tren thu muc goc cua du an. 
    """
    data_dir = os.path.join(ROOT_DIR, 'data')
    uploads_dir = os.path.join(data_dir, 'uploads')
    video_path = None
    
    # 1. Lay duong dan video tu tham so hoac mac dinh
    if len(sys.argv) > 1:
        # Neu truyen tham so, kiem tra ca duong dan tuong doi va tuyet doi
        input_arg = sys.argv[1]

        potential_path = os.path.join(uploads_dir, input_arg)

        if os.path.exists(potential_path):
            video_path = potential_path
        elif os.path.exists(input_arg): # Nếu gõ đường dẫn đầy đủ
            video_path = input_arg
        else:
            print(f"[-] Khong tim thay: {input_arg} trong thu muc uploads/")

    if not video_path:
            if os.path.exists(uploads_dir):
                files = [f for f in os.listdir(uploads_dir) if f.lower().endswith('.mp4')]
                if files:
                    print("\n[*] Goi y: Ban co the go 'python .\scripts\draw_zones.py <ten_file.mp4>'")
                    print("--- DANH SACH VIDEO HIEN CO ---")
                    for i, f in enumerate(files):
                        print(f"{i+1}. {f}")
                    
                    choice = input("\nNhap so thu tu de mo (mac dinh 1): ")
                    idx = int(choice) - 1 if choice.isdigit() and 0 < int(choice) <= len(files) else 0
                    video_path = os.path.join(uploads_dir, files[idx])

    if not video_path or not os.path.exists(video_path):
        return None, None

    # 2. Tu dong tao ten file JSON trong ROOT/data/
    video_filename = os.path.basename(video_path)
    video_name_only = os.path.splitext(video_filename)[0]
    
    data_dir = os.path.join(ROOT_DIR, 'data')
    os.makedirs(data_dir, exist_ok=True)
    json_path = os.path.join(data_dir, f"{video_name_only}_zones.json")
    
    return video_path, json_path

def main():
    global points, zones

    video_path, json_path = get_paths()
    
    if not video_path:
        print("LOI: Khong tim thay file video .mp4 nao trong thu muc uploads!")
        print(f"Hay kiem tra lai: {os.path.join(ROOT_DIR, 'uploads')}")
        return

    # Tai cau hinh cu neu co
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            try: zones = json.load(f)
            except: zones = {}

    cap = cv2.VideoCapture(video_path)
    # Nhảy qua các frame đầu để tránh màn hình đen
    cap.set(cv2.CAP_PROP_POS_FRAMES, 15)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print(f"LOI: OpenCV khong the doc frame tu: {video_path}")
        return

    cv2.namedWindow("Draw Zones", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Draw Zones", click_event)

    cv2.setWindowProperty("Draw Zones", cv2.WND_PROP_TOPMOST, 1)
    # Tùy chọn: Đợi 1ms để Windows kịp nhận diện
    cv2.waitKey(1) 
    # Tắt chế độ luôn trên cùng để bạn vẫn có thể chuyển đổi giữa các tab khác
    cv2.setWindowProperty("Draw Zones", cv2.WND_PROP_TOPMOST, 0)
    
    print("\n" + "="*45)
    print(f"PROJECT ROOT: {ROOT_DIR}")
    print(f"DANG MO: {os.path.basename(video_path)}")
    print(f"SE LUU VAO: {json_path}")
    print("-" * 45)
    print("PHIM TAT: 0-9 (Luu Zone), z (Undo), r (Reset), q (Luu & Thoat)")
    print("="*45)

    while True:
        display_frame = frame.copy()

        for name, pts in zones.items():
            cv2.polylines(display_frame, [np.array(pts, np.int32)], True, (0, 255, 0), 2)
            cv2.putText(display_frame, name, tuple(pts[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        for pt in points:
            cv2.circle(display_frame, pt, 5, (0, 0, 255), -1)
        if len(points) > 1:
            cv2.polylines(display_frame, [np.array(points)], False, (0, 0, 255), 2)

        cv2.imshow("Draw Zones", display_frame)
        key = cv2.waitKey(10) & 0xFF

        if ord('0') <= key <= ord('9'):
            if len(points) > 2:
                zones[f"zone_{chr(key)}"] = points.copy()
                points.clear()
        elif key == ord('z'):
            if points: points.pop()
            elif zones: zones.popitem()
        elif key == ord('r'):
            zones, points = {}, []
        elif key == ord('q'):
            break

    cv2.destroyAllWindows()
    with open(json_path, "w") as f:
        json.dump(zones, f, indent=4)
    print(f"\nDa luu thanh cong vao: {json_path}")

if __name__ == "__main__":
    main()