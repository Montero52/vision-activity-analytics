import os
import time
import logging
import pandas as pd
from flask import Flask, render_template, Response, request, redirect, url_for, send_file, jsonify, send_from_directory
from waitress import serve
from send2trash import send2trash
from src.camera import EmployeeTrackerEngine

# Import các thành phần đã được tinh chỉnh chuẩn chuyên gia
from config import Config
from src.database import (
    init_db, 
    create_new_session,
    get_latest_actions, 
    get_all_sessions, 
    get_employee_name_map, 
    update_employee_name, 
    import_employee_list,
    get_latest_session_id,
    get_report_data,
    get_db_connection,
    get_session_by_id,
)

# 1. Cấu hình Logging tập trung
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Giảm mức log của Waitress để làm nổi bật Performance Report của AI
logging.getLogger('waitress').setLevel(logging.WARNING)

app = Flask(__name__)
app.config.from_object(Config)

# Khởi tạo Engine AI với Class mới: EmployeeTrackerEngine
analytics = EmployeeTrackerEngine(model_path=app.config['MODEL_PATH'])

# --- 2. DASHBOARD & VIEW ROUTES ---

@app.route('/')
def index():
    """Main dashboard showing live status, logs, and file management."""
    try:
        # Đồng bộ Session ID hiện tại giữa AI Engine và Database
        current_id = analytics.current_session_id or get_latest_session_id()
        
        actions = get_latest_actions(limit=20, session_id=current_id)
        sessions = get_all_sessions()
        emp_map = get_employee_name_map() 

        # Quét thư mục để hiển thị danh sách video
        uploaded_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                          if f.endswith(('.mp4', '.avi', '.mov'))]
        
        result_files = [f for f in os.listdir(app.config['OUTPUT_FOLDER']) 
                        if f.startswith('result_') and f.endswith(('.mp4', '.avi'))]
        
        return render_template('index.html', 
                               actions=actions, 
                               sessions=sessions,
                               emp_map=emp_map,
                               uploaded_files=uploaded_files,
                               result_files=result_files,
                               current_session_id=current_id,
                               timestamp=int(time.time()))
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        return "Internal Server Error", 500

@app.route('/employees', methods=['POST'])
def update_employee():
    # Gọi hàm update_employee_name đã khôi phục
    emp_id = request.form.get('emp_id')
    full_name = request.form.get('full_name')
    if emp_id:
        update_employee_name(emp_id, full_name)
    return redirect(url_for('index'))

@app.route('/video_feed/<filename>')
def video_feed(filename):
    """Starts AI stream and initializes a new monitoring session."""
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(video_path):
        # Tạo session mới mỗi khi bấm xem video
        new_id = create_new_session(filename)
        analytics.start_new_analysis(video_path, session_id=new_id) 
        
        return Response(analytics.generate_stream(video_path),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Video not found", 404

# --- 3. VIDEO PROCESSING & LOG ANALYTICS ---

@app.route('/process_offline/<filename>')
def process_offline(filename):
    """Processes video in the background and saves annotated results."""
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(input_path):
        return "Input file missing", 404

    session_id = create_new_session(filename)
    output_filename = f"result_S{session_id}_{filename}"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    
    # Gọi hàm xử lý file đã được khôi phục và tinh chỉnh
    analytics.process_video_file(input_path, output_path, session_id=session_id)
    return redirect(url_for('index'))

@app.route('/get_video_logs/<filename>')
def get_video_logs(filename):
    """API for retrieving historical logs of a processed video."""
    try:
        # Trích xuất session_id từ tên file (Ví dụ: result_S15_video.mp4)
        session_id = filename.split('_')[1].replace('S', '')
        with get_db_connection() as conn:
            actions = conn.execute('''
                SELECT a.*, e.full_name FROM actions a 
                LEFT JOIN employees e ON a.employee_id = e.emp_id 
                WHERE a.session_id = ? ORDER BY a.timestamp ASC
            ''', (session_id,)).fetchall()
            return jsonify([dict(row) for row in actions])
    except Exception as e:
        logger.error(f"Log retrieval error: {e}")
        return jsonify([])
    

from send2trash import send2trash

# ROUTE 1: Chỉ xóa file kết quả phân tích
@app.route('/delete_output/<session_id>')
def delete_output(session_id):
    clean_id = session_id.replace('S', '')
    session_info = get_session_by_id(clean_id)
    
    if session_info:
        result_name = f"result_{session_id}_{session_info['video_name']}"
        path = os.path.join(app.config['OUTPUT_FOLDER'], result_name)
        
        if os.path.exists(path):
            send2trash(os.path.abspath(path))
            print(f"[SUCCESS] Đã đưa kết quả {result_name} vào thùng rác.")
            
    return redirect(url_for('index'))

@app.route('/delete_raw_upload/<path:filename>')
def delete_raw_upload(filename):
    print(f"[DEBUG] Yêu cầu xóa tệp tin thô: {filename}")
    
    # Đường dẫn tuyệt đối đến tệp trong thư mục uploads
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(file_path):
        try:
            # Chỉ đưa file vào thùng rác, không đụng đến Database
            send2trash(os.path.abspath(file_path))
            print(f"[SUCCESS] Đã đưa {filename} vào thùng rác.")
        except Exception as e:
            print(f"[ERROR] Không thể xóa tệp: {e}")
    else:
        print(f"[WARNING] Tệp tin không tồn tại: {file_path}")

    # Quay lại trang chính
    return redirect(url_for('index'))

# --- 4. HUMAN RESOURCES & REPORTS ---

@app.route('/import_employees', methods=['POST'])
def import_employees():
    """Bulk import employee data from CSV/Excel for recognition."""
    file = request.files.get('file')
    if file:
        try:
            df = pd.read_csv(file) if file.filename.endswith('.csv') else pd.read_excel(file)
            data_to_import = []
            for _, row in df.iterrows():
                # Map các cột theo chuẩn template của Duy Tân
                emp_id = row.get('Mã NV') or row.get('Ma NV')
                full_name = row.get('Họ Tên') or row.get('Ho Ten')
                if emp_id and full_name:
                    data_to_import.append((str(emp_id), str(full_name), 'Staff'))
            
            if data_to_import:
                import_employee_list(data_to_import)
        except Exception as e:
            logger.error(f"Bulk import failed: {e}")
    return redirect(url_for('index'))

# --- 2.1 THÊM ROUTE UPLOAD (Bị thiếu) ---
@app.route('/upload', methods=['POST'])
def upload_video():
    """Nhận video từ Dashboard và lưu vào thư mục upload."""
    if 'video' not in request.files:
        logger.error("No video part in request")
        return redirect(request.url)
    
    file = request.files['video']
    if file.filename == '':
        return redirect(request.url)

    if file:
        # Đảm bảo thư mục tồn tại trước khi lưu
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filename = file.filename
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        logger.info(f"Video uploaded successfully: {filename}")
        return redirect(url_for('index'))
    return redirect(request.url)

@app.route('/export_report')
def export_report():
    """Exports full activity history to an Excel report."""
    df = get_report_data()
    if df is not None:
        report_filename = f"Personnel_Report_{int(time.time())}.xlsx"
        report_path = os.path.join(app.config['REPORT_FOLDER'], report_filename)
        df.to_excel(report_path, index=False, engine='openpyxl')
        return send_file(report_path, as_attachment=True)
    return "No report data", 404


# Route này dùng để PHÁT video trên trình duyệt
@app.route('/view_output/<filename>')
def view_output(filename):
    return send_from_directory(
        app.config['OUTPUT_FOLDER'], 
        filename, 
        mimetype='video/mp4',
        as_attachment=False  # QUAN TRỌNG: Để False để trình duyệt cho phép phát
    )

# Giữ nguyên route này nếu bạn vẫn muốn nút tải về hoạt động riêng
@app.route('/download_output/<filename>')
def download_output(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    return send_file(file_path, as_attachment=True) if os.path.exists(file_path) else ("Not found", 404)

# --- 5. SYSTEM INITIALIZATION ---

# if __name__ == '__main__':
#     init_db() # Khởi tạo Database
#     app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    # Đảm bảo Database luôn sẵn sàng trước khi Server chạy
    init_db()
    
    # Terminal Header chuyên nghiệp cho buổi Demo
    print("\n" + "="*50)
    print("AI EMPLOYEE TRACKER - PRODUCTION SERVER")
    print("Status: RUNNING")
    print("Host: http://localhost:5000")
    print("Engine: OpenVINO Optimized (Intel CPU)")
    print("="*50 + "\n")
    
    # Triển khai bằng Waitress để đạt độ ổn định cao nhất (6 luồng)
    serve(app, host='0.0.0.0', port=5000, threads=6)