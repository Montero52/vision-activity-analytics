import cv2
import json
import numpy as np
import os
import time
import psutil
import logging
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO
from src.database import log_action, create_new_session, get_employee_name_map
from config import Config
from moviepy.editor import VideoFileClip

# Cấu hình Logging chuẩn công nghiệp
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmployeeTrackerEngine:
    """
    Core engine for AI-based employee monitoring.
    Optimized for Intel CPUs using OpenVINO and production-ready with Waitress.
    """
    
    def __init__(self, model_path=None):
        """Initialize AI model, load fonts, and prepare system states."""
        # 1. Hardware & Model Configuration
        self.model = YOLO(model_path or Config.MODEL_PATH, task='detect')

        self.tracker_config = Config.TRACKER_CONFIG
        # 2. Performance Tuning Constants
        self.TARGET_FPS = Config.TARGET_FPS
        self.SKIP_FRAMES = Config.SKIP_FRAMES
        self.CONF_THRESHOLD = Config.CONF_THRESHOLD
        self.IMG_SIZE = Config.IMG_SIZE
        self.PATIENCE_LIMIT = Config.PATIENCE_LIMIT
        self.MIN_WORK_DURATION = Config.MIN_WORK_DURATION

        self._warm_up_model()
        
        # 3. Graphics & Asset Caching
        self.font_path = self._get_font_path()
        self.font_normal = self._load_font(20)
        self.font_small = self._load_font(16)
        
        # 4. Operational States
        self.current_session_id = None
        self.zones = []
        self.zone_names = []
        self.emp_name_map = {}
        self.refresh_employee_data()
        self.reset_state()
        
        # 5. Benchmarking Metrics
        self.perf_stats = {
            "inference_times": [],
            "total_frame_times": [],
            "cpu_usages": []
        }
        self.prev_time = time.time()

    # --- HÀM TIỆN ÍCH (HELPERS) ---

    def _warm_up_model(self):
        """
        Warm-up dành riêng cho OpenVINO. 
        Kích hoạt tập lệnh tối ưu của Intel (AVX-512/VNNI) trước khi stream.
        """
        try:
            # OpenVINO rất nhạy cảm với input shape
            input_size = self.IMG_SIZE 
            logger.info(f"[*] OpenVINO Warm-up: Đang tối ưu hóa kernels cho CPU (size={input_size})...")
            
            dummy_frame = np.zeros((input_size, input_size, 3), dtype=np.uint8)
            
            # Chạy thử 2 lần (OpenVINO thường cần lần 1 để compile, lần 2 để ổn định)
            for i in range(2):
                self.model.predict(
                    dummy_frame, 
                    imgsz=input_size, 
                    device="cpu", 
                    verbose=False
                )
            logger.info("[+] OpenVINO đã 'nóng'. CPU đã sẵn sàng xử lý tốc độ cao!")
        except Exception as e:
            logger.error(f"[-] Lỗi khởi tạo OpenVINO: {e}")

    def _get_font_path(self):
        """Find Vietnamese-supported system font."""
        paths = ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "arial.ttf"]
        return next((p for p in paths if os.path.exists(p)), None)

    def _load_font(self, size):
        """Safely load font with a fallback to default."""
        try:
            return ImageFont.truetype(self.font_path, size) if self.font_path else ImageFont.load_default()
        except Exception as e:
            logger.warning(f"Font loading failed: {e}. Fallback to default.")
            return ImageFont.load_default()

    def refresh_employee_data(self):
        """Sync employee names from the database for visualization."""
        try:
            self.emp_name_map = get_employee_name_map()
        except Exception as e:
            logger.error(f"Database sync failed: {e}")
            self.emp_name_map = {}

    def reset_state(self):
        """Reset internal buffers for a fresh analysis session."""
        self.frame_count = 0
        self.zone_status = {} # {idx: {"start": frame, "patience": int, "logged": bool}}
        self.last_results = None

    # --- LOGIC XỬ LÝ CHÍNH ---

    def start_new_analysis(self, video_path, session_id=None):
        """Load zone configurations and start a new monitoring session."""
        self.refresh_employee_data()
        
        filename = os.path.basename(video_path)
        name_only = os.path.splitext(filename)[0]
        json_path = os.path.join(Config.DATA_DIR, f"{name_only}_zones.json")
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.zones = [np.array(v, dtype=np.int32) for v in data.values()]
                self.zone_names = list(data.keys())
        
        self.reset_state()
        self.current_session_id = session_id or create_new_session(filename)
        logger.info(f"Analysis started: Session {self.current_session_id} for {filename}")

    def _process_frame(self, frame):
        """Single frame processing pipeline: Inference -> Tracking -> Visualization."""
        now = time.time()
        if self.frame_count > 0:
            self.perf_stats["total_frame_times"].append((now - self.prev_time) * 1000)
        self.prev_time = now
        self.frame_count += 1
        
        # 1. AI Inference with Frame Skipping
        if (self.frame_count % (self.SKIP_FRAMES + 1) == 0):
            inf_start = time.time()
            results = self.model.track(
                frame, persist=True, tracker = self.tracker_config,
                device="cpu", imgsz=self.IMG_SIZE, classes=[0],
                conf=self.CONF_THRESHOLD, iou=0.3, verbose=False
            )
            self.last_results = results[0] if (results and len(results[0].boxes) > 0) else None
            
            self.perf_stats["inference_times"].append((time.time() - inf_start) * 1000)
            self.perf_stats["cpu_usages"].append(psutil.cpu_percent())

        # 2. Graphical Drawing (PIL Optimized)
        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        occupied_zones = []

        if self.last_results:
            boxes = self.last_results.boxes.xyxy.cpu().numpy()
            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                #cx, cy = (x1 + x2) // 2, (y1 + y2) // 2 
                w, h = x2 - x1, y2 - y1
                area = w * h
                MAX_NORMAL_AREA = 22000 

                # 2. NGƯỠNG DIỆN TÍCH (MAX_AREA)
                # Ở góc cam này, một người bình thường thường < 20,000 px.
                # Nếu gộp 2 người, diện tích sẽ vọt lên khoảng 30,000 - 45,000 px.
                if area > MAX_NORMAL_AREA: 
                    # draw.rectangle([x1, y1, x2, y2], outline=(255, 0, 255), width=3)
                    # draw.text((x1, y1 - 45), f"AREA ERR: {area}", font=self.font_small, fill=(255, 0, 255))
                    # print(f"--- LOẠI BỎ BOX GỘP: Area={area} (To gấp đôi bình thường) ---")
                    continue 

                # 3. Kết hợp một chút Ratio nhưng ở ngưỡng rất an toàn (> 1.2 - Hình chữ nhật ngang)
                if (w / h) > 1.2:
                    continue
                        
                cx = (x1 + x2) // 2
                cy = y1 + int((y2 - y1) * 0.25) 
                check_point = (cx, cy)

                in_zone = False
                for idx, poly in enumerate(self.zones):
                    if cv2.pointPolygonTest(poly, check_point, False) >= 0:
                        occupied_zones.append(idx)
                        in_zone = True
                        
                        emp_code = f"NV-{idx + 1}"
                        name = self.emp_name_map.get(emp_code, "Chưa rõ")
                        draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0), width=2)
                        draw.text((x1, y1 - 25), f"{emp_code} ({name})", font=self.font_normal, fill=(0, 255, 0))
                        
                        if idx not in self.zone_status:
                            self.zone_status[idx] = {"start": self.frame_count, "patience": 0, "logged": False}
                        else:
                            self.zone_status[idx]["patience"] = 0 
                        break
                
                if not in_zone:
                    draw.rectangle([x1, y1, x2, y2], outline=(255, 255, 255), width=1)

        # 3. Business Logic Logging
        self._handle_logging(occupied_zones, 1.0/30.0)

        # 4. Polygons & Zone Labels
        for idx, poly in enumerate(self.zones):
            color = (0, 255, 0) if idx in occupied_zones else (255, 0, 0)
            draw.polygon([tuple(p) for p in poly], outline=color, width=2)
            draw.text((poly[0][0], poly[0][1] - 25), self.zone_names[idx], font=self.font_small, fill=color)
            
        # Revert to OpenCV format
        final_frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        if self.frame_count % 100 == 0:
            self._print_performance_report()
            
        return final_frame

    def _handle_logging(self, occupied_zones, frame_dur):
        for idx in range(len(self.zones)):
            emp_code = f"NV-{idx + 1}"
            curr_v_time = self.frame_count * frame_dur
            # Định dạng thời gian 00:00:00
            time_str = time.strftime('%H:%M:%S', time.gmtime(curr_v_time))

            if idx in occupied_zones:
                state = self.zone_status[idx]
                if not state["logged"]:
                    # Tính duration dựa trên start_frame
                    duration = (self.frame_count - state["start"]) * frame_dur
                    if duration >= self.MIN_WORK_DURATION:
                        log_action(emp_code, f"Làm việc (tại {time_str})", self.current_session_id)
                        state["logged"] = True
            elif idx in self.zone_status:
                self.zone_status[idx]["patience"] += 1
                if self.zone_status[idx]["patience"] > self.PATIENCE_LIMIT:
                    state = self.zone_status[idx]
                    if state["logged"]:
                        total = (self.frame_count - state["start"]) * frame_dur
                        log_action(emp_code, f"Rời bàn (tại {time_str} - Tổng: {int(total)}s)", self.current_session_id)
                    del self.zone_status[idx]

    def _print_performance_report(self):
        """Displays real-time benchmarking stats in the terminal."""
        avg_inf = np.mean(self.perf_stats["inference_times"]) if self.perf_stats["inference_times"] else 0
        avg_total = np.mean(self.perf_stats["total_frame_times"]) if self.perf_stats["total_frame_times"] else 0
        avg_cpu = np.mean(self.perf_stats["cpu_usages"]) if self.perf_stats["cpu_usages"] else 0
        real_fps = 1000.0 / avg_total if avg_total > 0 else 0

        print(f"\n{'='*35}")
        print(f"PERFORMANCE REPORT (Frame {self.frame_count})")
        print(f"AI Inference      : {avg_inf:.2f} ms")
        print(f"Total Process/Fr  : {avg_total:.2f} ms")
        print(f"Real-time FPS     : {real_fps:.1f} FPS")
        print(f"CPU Utilization   : {avg_cpu:.1f} %")
        print(f"{'='*35}\n")

    # --- STREAMING & FILE EXPORT ---

    def generate_stream(self, video_path):
        """Generator for Flask web streaming with FPS capping."""
        cap = cv2.VideoCapture(video_path)
        self.start_new_analysis(video_path)
        target_time = 1.0 / self.TARGET_FPS
        t_start = time.time()

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                frame = self._process_frame(frame)
                _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                
                # Dynamic Sync to lock 15 FPS
                elapsed = time.time() - t_start
                if target_time - elapsed > 0:
                    time.sleep(target_time - elapsed)
                self.perf_stats["total_frame_times"].append((time.time() - t_start) * 1000)
                t_start = time.time()
        finally:
            cap.release()

    def process_video_file(self, in_p, out_p, session_id=None): 
        """Processes video file and converts to Web-compatible H.264."""
        cap = cv2.VideoCapture(in_p)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        w, h = int(cap.get(3)), int(cap.get(4))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(out_p, fourcc, fps, (w, h))
        
        self.start_new_analysis(in_p, session_id=session_id) 
        logger.info(f"Processing video file: {in_p}")
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                out.write(self._process_frame(frame))
        finally:
            cap.release()
            out.release()

        # Web-Ready H.264 Conversion logic
        try:
            temp_convert = out_p.replace(".mp4", "_web.mp4")
            clip = VideoFileClip(out_p)
            clip.write_videofile(temp_convert, codec="libx264", audio=False, verbose=False, logger=None)
            clip.close()
            os.remove(out_p)
            os.rename(temp_convert, out_p)
            logger.info("Video conversion to H.264 successful!")
        except Exception as e:
            logger.error(f"H.264 conversion failed: {e}")