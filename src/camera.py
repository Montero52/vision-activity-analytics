import cv2
import json
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO
from src.database import log_action, create_new_session, get_employee_name_map
from config import Config
from moviepy.editor import VideoFileClip

class VideoAnalytics:
    def __init__(self, model_path=None):
        # 1. Khởi tạo Model & Cấu hình
        self.model = YOLO(model_path or Config.MODEL_PATH)
        self.tracker_config = "models/bytetrack.yaml"
        self.font_path = self._get_font_path()
        
        # 2. Tham số Logic (Càng cao càng ổn định)
        self.min_duration = 3        # giây tối thiểu để tính là đang ngồi
        self.patience_limit = 200    # frames đợi để xác nhận đã rời đi
        self.skip_frames = 1         # số frame bỏ qua để tăng tốc AI
        
        # 3. Trạng thái hệ thống
        self.current_session_id = None
        self.zones = []              # Polygons
        self.zone_names = []         # Tên vùng
        self.fps = 30
        self.emp_name_map = {}
        
        self.refresh_employee_data()
        self.reset_state()

    # --- HÀM TIỆN ÍCH (HELPER) ---

    def _get_font_path(self):
        """Tự động tìm font phù hợp trên hệ thống"""
        paths = ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "arial.ttf"]
        for p in paths:
            if os.path.exists(p): return p
        return None

    def refresh_employee_data(self):
        """Đồng bộ danh sách nhân viên từ Database"""
        try:
            self.emp_name_map = get_employee_name_map()
        except:
            self.emp_name_map = {}

    def reset_state(self):
        """Xóa sạch bộ nhớ đệm cho phiên làm việc mới"""
        self.frame_count = 0
        self.zone_status = {} # {idx: {"start": frame, "patience": int, "logged": bool}}
        self.last_results = None

    def draw_vietnamese_text(self, img, text, position, font_size=20, color=(0, 255, 0)):
        """Vẽ chữ tiếng Việt (PIL hỗ trợ tốt hơn OpenCV)"""
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        try:
            font = ImageFont.truetype(self.font_path, font_size)
        except:
            font = ImageFont.load_default()
        
        draw.text(position, text, font=font, fill=color)
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    # --- LOGIC CHÍNH ---

    def start_new_analysis(self, video_path, session_id=None):
        """Khởi động lượt phân tích mới"""
        filename = os.path.basename(video_path)
        name_only = os.path.splitext(filename)[0]
        json_path = os.path.join(Config.DATA_DIR, f"{name_only}_zones.json")
        
        # Load vùng zone từ file JSON
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.zones = [np.array(v, dtype=np.int32) for v in data.values()]
                self.zone_names = list(data.keys())
        
        self.refresh_employee_data()
        self.reset_state()
        self.current_session_id = session_id or create_new_session(filename)

    def _process_frame(self, frame):
        """Hàm xử lý frame đơn lẻ (Trung tâm của AI)"""
        self.frame_count += 1
        frame_dur = 1.0 / (self.fps if self.fps > 0 else 30)
        
        # 1. Chạy AI Tracking (Có thể bỏ qua frame để mượt hơn)
        if (self.frame_count % (self.skip_frames + 1) == 0):
            results = self.model.track(frame, persist=True, tracker=self.tracker_config, 
                                      classes=[0], conf=0.3, verbose=False)
            self.last_results = results[0] if (results and len(results[0].boxes) > 0) else None

        occupied_zones = []

        # 2. Phân tích vùng và vẽ khung
        if self.last_results:
            boxes = self.last_results.boxes.xyxy.cpu().numpy()
            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2 
                
                in_zone = False
                for idx, poly in enumerate(self.zones):
                    if cv2.pointPolygonTest(poly, (cx, cy), False) >= 0:
                        occupied_zones.append(idx)
                        in_zone = True
                        
                        # Hiển thị thông tin
                        emp_code = f"NV-{idx + 1}"
                        display_text = f"{emp_code} ({self.emp_name_map.get(emp_code, 'Chưa rõ')})"
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        frame = self.draw_vietnamese_text(frame, display_text, (x1, y1 - 25))
                        
                        # Cập nhật trạng thái vùng
                        if idx not in self.zone_status:
                            self.zone_status[idx] = {"start": self.frame_count, "patience": 0, "logged": False}
                        else:
                            self.zone_status[idx]["patience"] = 0 
                        break
                
                if not in_zone:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)

        # 3. Ghi nhật ký (Log Logic)
        self._handle_logging(occupied_zones, frame_dur)

        # 4. Vẽ ranh giới các vùng Zone
        for idx, poly in enumerate(self.zones):
            color = (0, 255, 0) if idx in occupied_zones else (0, 0, 255)
            cv2.polylines(frame, [poly], True, color, 2)
            frame = self.draw_vietnamese_text(frame, self.zone_names[idx], 
                                              (poly[0][0], poly[0][1] - 25), 16, color)
        return frame

    def _handle_logging(self, occupied_zones, frame_dur):
        """Tách riêng logic ghi log cho sạch code"""
        for idx in range(len(self.zones)):
            emp_code = f"NV-{idx + 1}"
            
            if idx in occupied_zones:
                state = self.zone_status[idx]
                if not state["logged"]:
                    duration = (self.frame_count - state["start"]) * frame_dur
                    if duration >= self.min_duration:
                        log_action(emp_code, f"Làm việc: {self.zone_names[idx]}", self.current_session_id)
                        state["logged"] = True
            
            elif idx in self.zone_status:
                self.zone_status[idx]["patience"] += 1
                if self.zone_status[idx]["patience"] > self.patience_limit:
                    state = self.zone_status[idx]
                    if state["logged"]:
                        total = (self.frame_count - state["start"]) * frame_dur
                        log_action(emp_code, f"Rời bàn (Tổng: {int(total)}s)", self.current_session_id)
                    del self.zone_status[idx]

    # --- PHÁT STREAM VÀ XUẤT FILE ---

    def generate_stream(self, video_path):
        cap = cv2.VideoCapture(video_path)
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.start_new_analysis(video_path)
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                frame = self._process_frame(frame)
                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        finally:
            cap.release()

    def process_video_file(self, in_p, out_p, session_id=None): 
        cap = cv2.VideoCapture(in_p)
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        w, h = int(cap.get(3)), int(cap.get(4))
        
        # Codec mp4v để tối ưu việc ghi file trên Windows
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(out_p, fourcc, self.fps, (w, h))
        
        self.start_new_analysis(in_p, session_id=session_id) 
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                out.write(self._process_frame(frame))
        finally:
            cap.release()
            out.release()
        try:
            temp_convert = out_p.replace(".mp4", "_web.mp4")
            clip = VideoFileClip(out_p)
            # codec="libx264" là chuẩn "vàng" để xem được trên mọi trình duyệt
            clip.write_videofile(temp_convert, codec="libx264", audio=False, verbose=False, logger=None)
            clip.close()
            
            # Xóa file cũ, đổi tên file web thành file chính
            os.remove(out_p)
            os.rename(temp_convert, out_p)
            print("AI: Đã chuyển đổi video sang chuẩn Web H.264 thành công!")
        except Exception as e:
            print(f"Lỗi chuyển đổi chuẩn Web: {e}")
