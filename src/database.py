import sqlite3
from datetime import datetime
import pandas as pd # pip install pandas
import os

# Đường dẫn database
DB_PATH = 'data/employees.db'

# Đảm bảo folder data luôn tồn tại
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON') 
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    try:
        with get_db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_name TEXT NOT NULL,
                    start_time DATETIME DEFAULT (datetime('now','localtime'))
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    emp_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    position TEXT
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    employee_id TEXT NOT NULL,
                    action TEXT,
                    timestamp DATETIME DEFAULT (datetime('now','localtime')),
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (employee_id) REFERENCES employees(emp_id)
                )
            ''')
            seed_data(conn)
    except Exception as e:
        print(f"Lỗi khởi tạo Database: {e}")

def seed_data(conn):
    """Thêm vài nhân viên mẫu nếu bảng đang trống"""
    check = conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
    if check == 0:
        sample_data = [
            ('NV-1', 'Nguyễn Văn A', 'Developer'),
            ('NV-2', 'Trần Thị B', 'Accountant'),
            ('NV-3', 'Lê Văn C', 'Designer')
        ]
        conn.executemany('INSERT INTO employees (emp_id, full_name, position) VALUES (?, ?, ?)', sample_data)
        conn.commit()

def import_employee_list(data_list):
    """Nạp danh sách nhân viên vào Database. data_list: list of tuples (id, name, pos)"""
    try:
        with get_db_connection() as conn:
            # Sử dụng INSERT OR REPLACE để cập nhật nếu trùng ID
            conn.executemany('''
                INSERT OR REPLACE INTO employees (emp_id, full_name, position)
                VALUES (?, ?, ?)
            ''', data_list)
            conn.commit()
            print(f"Hệ thống: Đã nạp thành công {len(data_list)} nhân viên.")
            return True
    except Exception as e:
        print(f"Lỗi nạp danh sách vào DB: {e}")
        return False
    
# --- CÁC HÀM BỔ SUNG CHO CAMERA.PY ---

def get_employee_name_map():
    """Trả về từ điển: {'NV-1': 'Nguyễn Văn A', ...} để AI nạp vào RAM"""
    try:
        with get_db_connection() as conn:
            rows = conn.execute('SELECT emp_id, full_name FROM employees').fetchall()
            return {row['emp_id']: row['full_name'] for row in rows}
    except Exception as e:
        print(f"Lỗi lấy danh sách nhân viên: {e}")
        return {}

def update_employee_name(emp_id, new_name):
    """Cập nhật tên nhân viên cho một mã bàn cụ thể"""
    try:
        with get_db_connection() as conn:
            conn.execute('UPDATE employees SET full_name = ? WHERE emp_id = ?', (new_name, emp_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"Lỗi cập nhật tên: {e}")
        return False
    

def sync_employees_from_file():
    file_path = 'employees.csv'
    if not os.path.exists(file_path):
        print("Lỗi: Không tìm thấy file danh sách nhân viên!")
        return
    
    # Đọc dữ liệu từ file
    df = pd.read_csv(file_path) 
    
    with get_db_connection() as conn:
        for _, row in df.iterrows():
            conn.execute('''
                INSERT OR REPLACE INTO employees (emp_id, full_name, position)
                VALUES (?, ?, ?)
            ''', (row['emp_id'], row['full_name'], row['position']))
        conn.commit()
    print(f"Hệ thống: Đã đồng bộ {len(df)} nhân viên từ file vào Database.")

# --- CÁC HÀM CŨ GIỮ NGUYÊN ---

def create_new_session(video_name):
    """LUÔN tạo một phiên mới - Dùng cho Live AI hoặc bắt đầu lượt xử lý mới"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("INSERT INTO sessions (video_name) VALUES (?)", (video_name,))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Lỗi tạo session mới: {e}")
        return None

def get_or_create_session(video_name):
    """Tìm session cũ, nếu không có mới tạo - Dùng cho các trường hợp cần đồng bộ"""
    try:
        with get_db_connection() as conn:
            query = "SELECT id FROM sessions WHERE video_name = ? ORDER BY id DESC LIMIT 1"
            row = conn.execute(query, (video_name,)).fetchone()
            if row:
                return row['id']
            return create_new_session(video_name)
    except Exception as e:
        return None

def get_report_data():
    """Lấy dữ liệu báo cáo đầy đủ thông tin nhất"""
    try:
        with get_db_connection() as conn:
            # Truy vấn kết hợp: Mã NV, Tên NV, Tên Video, Session, Hành động, Thời gian
            sql = '''
                SELECT 
                    s.id AS "Mã Phiên",
                    s.video_name AS "Tên Video",
                    e.emp_id AS "Mã NV",
                    e.full_name AS "Họ Tên Nhân Viên",
                    a.action AS "Hành Động",
                    a.timestamp AS "Thời Gian Ghi Nhận"
                FROM actions a
                JOIN sessions s ON a.session_id = s.id
                JOIN employees e ON a.employee_id = e.emp_id
                ORDER BY s.id DESC, a.timestamp ASC
            '''
            # Dùng pandas để đọc trực tiếp từ SQL sang DataFrame
            return pd.read_sql_query(sql, conn)
    except Exception as e:
        print(f"Lỗi truy vấn báo cáo: {e}")
        return None
    
 # --- GHI NHẬT KÝ ---   
def log_action(employee_id, action, session_id):
    if session_id is None: return
    try:
        with get_db_connection() as conn:
            # 1. KIỂM TRA: Nếu nhân viên chưa tồn tại thì tự động thêm vào để tránh lỗi Foreign Key
            conn.execute('''
                INSERT OR IGNORE INTO employees (emp_id, full_name, position) 
                VALUES (?, ?, ?)
            ''', (employee_id, f"Nhân viên mới ({employee_id})", "Chưa phân loại"))
            
            # 2. GHI LOG: Bây giờ chắc chắn sẽ thành công
            conn.execute(
                'INSERT INTO actions (session_id, employee_id, action, timestamp) VALUES (?, ?, ?, datetime("now","localtime"))',
                (session_id, employee_id, action)
            )
            conn.commit()
    except Exception as e:
        print(f"Lỗi ghi log: {e}") # Nếu vẫn lỗi, hãy kiểm tra session_id có tồn tại không

# --- TRUY VẤN DỮ LIỆU ---

def get_latest_actions(limit=20, session_id=None):
    try:
        with get_db_connection() as conn:
            sql = 'SELECT a.*, e.full_name FROM actions a LEFT JOIN employees e ON a.employee_id = e.emp_id'
            if session_id:
                # BẮT BUỘC lọc theo session_id để không lấy rác của video cũ
                cursor = conn.execute(sql + ' WHERE a.session_id = ? ORDER BY a.timestamp DESC LIMIT ?', (session_id, limit))
            else:
                cursor = conn.execute(sql + ' ORDER BY a.timestamp DESC LIMIT ?', (limit,))
            return cursor.fetchall()
    except Exception as e:
        return []

def get_all_sessions():
    try:
        with get_db_connection() as conn:
            cursor = conn.execute('SELECT * FROM sessions ORDER BY start_time DESC')
            return cursor.fetchall()
    except Exception as e:
        print(f"Lỗi truy vấn session: {e}")
        return []   
    
def get_latest_session_id():
    """Lấy ID của phiên làm việc mới nhất"""
    try:
        with get_db_connection() as conn:
            row = conn.execute('SELECT id FROM sessions ORDER BY id DESC LIMIT 1').fetchone()
            return row['id'] if row else None
    except Exception as e:
        print(f"Lỗi lấy session mới nhất: {e}")
        return None