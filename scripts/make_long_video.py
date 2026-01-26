import cv2

# CẤU HÌNH
INPUT_FILE = 'uploads/input.mp4'  # Video 12s của bạn
OUTPUT_FILE = 'uploads/long_video.mp4'
LOOP_COUNT = 10  # Lặp lại 10 lần (12s x 10 = 120s = 2 phút)

def loop_video():
    cap = cv2.VideoCapture(INPUT_FILE)
    if not cap.isOpened():
        print(f"Lỗi: Không đọc được file {INPUT_FILE}")
        return

    # Lấy thông số video gốc
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Tạo video đầu ra
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(OUTPUT_FILE, fourcc, fps, (width, height))

    print(f"Đang xử lý... (Mục tiêu: {LOOP_COUNT} vòng lặp)")

    for i in range(LOOP_COUNT):
        print(f" - Đang ghép vòng thứ {i+1}...")
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Tua lại từ đầu
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

    cap.release()
    out.release()
    print(f"Xong! Video mới đã lưu tại: {OUTPUT_FILE}")

if __name__ == "__main__":
    loop_video()