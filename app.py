import os
import time
import pandas as pd
from flask import Flask, render_template, Response, request, redirect, url_for, send_file, jsonify
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
    get_report_data

)
from src.camera import VideoAnalytics

app = Flask(__name__)
app.config.from_object(Config)

# Khởi tạo AI với cấu hình từ Config
analytics = VideoAnalytics(model_path=app.config['MODEL_PATH'])

# --- 1. DASHBOARD & DISPLAY ---

@app.route('/')
def index():
    """Trang chủ: Quản lý Dashboard và Video"""
    current_id = analytics.current_session_id or get_latest_session_id()
    
    actions = get_latest_actions(limit=20, session_id=current_id)
    sessions = get_all_sessions()
    emp_map = get_employee_name_map() 

    # Quét danh sách file
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

@app.route('/video_feed/<filename>')
def video_feed(filename):
    """Phát luồng Live AI và tạo phiên mới"""
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(video_path):
        new_id = create_new_session(filename)
        analytics.start_new_analysis(video_path, session_id=new_id) 
        return Response(analytics.generate_stream(video_path),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Video not found", 404

# --- 2. XỬ LÝ VIDEO & LOGS ---

@app.route('/process_offline/<filename>')
def process_offline(filename):
    """Xử lý video lưu file kết quả"""
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(input_path):
        return "File không tồn tại", 404

    session_id = create_new_session(filename)
    output_filename = f"result_S{session_id}_{filename}"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    
    analytics.process_video_file(input_path, output_path, session_id=session_id)
    return redirect(url_for('index'))

@app.route('/get_video_logs/<filename>')
def get_video_logs(filename):
    """API lấy log cũ cho chức năng 'Xem KQ'"""
    from src.database import get_db_connection
    try:
        session_id = filename.split('_')[1].replace('S', '')
        with get_db_connection() as conn:
            actions = conn.execute('''
                SELECT a.*, e.full_name FROM actions a 
                LEFT JOIN employees e ON a.employee_id = e.emp_id 
                WHERE a.session_id = ? ORDER BY a.timestamp ASC
            ''', (session_id,)).fetchall()
            return jsonify([dict(row) for row in actions])
    except:
        return jsonify([])

# --- 3. QUẢN LÝ FILE & BÁO CÁO ---

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('video')
    if file:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    return redirect(url_for('index'))

@app.route('/download_output/<filename>')
def download_output(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    return send_file(file_path, as_attachment=True) if os.path.exists(file_path) else ("Not found", 404)

@app.route('/export_report')
def export_report():
    df = get_report_data()
    if df is not None:
        report_filename = f"Bao_Cao_Nhan_Su_{int(time.time())}.xlsx"
        report_path = os.path.join(app.config['REPORT_FOLDER'], report_filename)
        df.to_excel(report_path, index=False)
        return send_file(report_path, as_attachment=True)
    return "No data", 404

# --- 4. QUẢN LÝ NHÂN SỰ (IMPORT/UPDATE) ---

@app.route('/employees', methods=['POST'])
def update_employee():
    """Cập nhật tên lẻ cho từng nhân viên"""
    emp_id = request.form.get('emp_id')
    full_name = request.form.get('full_name')
    if emp_id:
        update_employee_name(emp_id, full_name)
    return redirect(url_for('index'))

@app.route('/import_employees', methods=['POST'])
def import_employees():
    """Import hàng loạt từ CSV/Excel (Tính năng quan trọng bị thiếu)"""
    file = request.files.get('file')
    if file:
        try:
            df = pd.read_csv(file) if file.filename.endswith('.csv') else pd.read_excel(file)
            data_to_import = []
            for _, row in df.iterrows():
                # Lấy đúng tên cột như trong file mẫu của bạn
                emp_id = row.get('Mã NV') or row.get('Ma NV')
                full_name = row.get('Họ Tên') or row.get('Ho Ten')
                if emp_id and full_name:
                    data_to_import.append((str(emp_id), str(full_name), 'Nhân viên'))
            
            if data_to_import:
                import_employee_list(data_to_import)
        except Exception as e:
            print(f"Lỗi Import: {e}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db() # Khởi tạo Database
    app.run(debug=True, host='0.0.0.0', port=5000)