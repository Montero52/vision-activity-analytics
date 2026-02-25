import sqlite3
import os
import logging
import pandas as pd
from config import Config

# Cấu hình logging đồng bộ với hệ thống
logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Establishes a connection to the SQLite database with optimized settings.
    Returns:
        sqlite3.Connection: Database connection object.
    """
    try:
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
        
        conn = sqlite3.connect(Config.DB_PATH)
        conn.execute('PRAGMA foreign_keys = ON') # Enforce relational integrity
        conn.row_factory = sqlite3.Row           # Access columns by name
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def init_db():
    """Initializes the database schema if tables do not exist."""
    try:
        with get_db_connection() as conn:
            # 1. Sessions table: Track individual monitoring runs
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_name TEXT NOT NULL,
                    start_time DATETIME DEFAULT (datetime('now','localtime'))
                )
            ''')
            
            # 2. Employees table: Master data of workers
            conn.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    emp_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    position TEXT
                )
            ''')

            # 3. Actions table: Activity logs with foreign key constraints
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
            _seed_sample_data(conn)
            logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}")

def _seed_sample_data(conn):
    """Internal helper to insert initial data if the employee table is empty."""
    check = conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
    if check == 0:
        sample_data = [
            ('NV-1', 'Nguyễn Văn A', 'Developer'),
            ('NV-2', 'Trần Thị B', 'Accountant'),
            ('NV-3', 'Lê Văn C', 'Designer')
        ]
        conn.executemany('INSERT INTO employees (emp_id, full_name, position) VALUES (?, ?, ?)', sample_data)
        conn.commit()
        logger.info("Sample employee data seeded.")

# --- EMPLOYEE MANAGEMENT ---

def get_employee_name_map():
    """
    Fetches employee ID to Name mapping for AI inference caching.
    Returns:
        dict: {emp_id: full_name}
    """
    try:
        with get_db_connection() as conn:
            rows = conn.execute('SELECT emp_id, full_name FROM employees').fetchall()
            return {row['emp_id']: row['full_name'] for row in rows}
    except Exception as e:
        logger.error(f"Error fetching employee map: {e}")
        return {}
    
def update_employee_name(emp_id, new_name):
    """Cập nhật tên nhân viên (Hàm này đã được khôi phục)."""
    try:
        with get_db_connection() as conn:
            conn.execute('UPDATE employees SET full_name = ? WHERE emp_id = ?', (new_name, emp_id))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Lỗi cập nhật tên: {e}")
        return False
    
def import_employee_list(data_list):
    """
    Bulk inserts or updates employee records.
    Args:
        data_list (list): List of tuples (emp_id, full_name, position)
    """
    try:
        with get_db_connection() as conn:
            conn.executemany('''
                INSERT OR REPLACE INTO employees (emp_id, full_name, position)
                VALUES (?, ?, ?)
            ''', data_list)
            conn.commit()
            logger.info(f"Successfully imported {len(data_list)} employees.")
            return True
    except Exception as e:
        logger.error(f"Bulk import failed: {e}")
        return False

def sync_employees_from_file(file_path='employees.csv'):
    """Synchronizes employee database with a CSV file."""
    if not os.path.exists(file_path):
        logger.warning(f"Sync failed: File {file_path} not found.")
        return
    
    try:
        df = pd.read_csv(file_path) 
        with get_db_connection() as conn:
            for _, row in df.iterrows():
                conn.execute('''
                    INSERT OR REPLACE INTO employees (emp_id, full_name, position)
                    VALUES (?, ?, ?)
                ''', (row['emp_id'], row['full_name'], row['position']))
            conn.commit()
        logger.info(f"Synchronized {len(df)} records from {file_path}.")
    except Exception as e:
        logger.error(f"File sync error: {e}")

# --- SESSION & LOGGING LOGIC ---

def create_new_session(video_name):
    """Creates a unique monitoring session and returns its ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("INSERT INTO sessions (video_name) VALUES (?)", (video_name,))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Failed to create session for {video_name}: {e}")
        return None

def get_latest_session_id():
    """Lấy ID phiên mới nhất (Hàm này đã được khôi phục)."""
    try:
        with get_db_connection() as conn:
            row = conn.execute('SELECT id FROM sessions ORDER BY id DESC LIMIT 1').fetchone()
            return row['id'] if row else None
    except Exception as e:
        logger.error(f"Lỗi lấy session ID: {e}")
        return None
    
def log_action(employee_id, action, session_id):
    """Records an employee action into the database with automatic member registration."""
    if session_id is None:
        return
        
    try:
        with get_db_connection() as conn:
            # Auto-register unknown employees to prevent Foreign Key violations
            conn.execute('''
                INSERT OR IGNORE INTO employees (emp_id, full_name, position) 
                VALUES (?, ?, ?)
            ''', (employee_id, f"Auto-Registered ({employee_id})", "Unknown"))
            
            conn.execute(
                'INSERT INTO actions (session_id, employee_id, action) VALUES (?, ?, ?)',
                (session_id, employee_id, action)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Action logging failed for {employee_id}: {e}")

# --- REPORTING & QUERYING ---

def get_report_data():
    """Retrieves a comprehensive report using Pandas for easier data analysis."""
    try:
        with get_db_connection() as conn:
            sql = '''
                SELECT 
                    s.id AS "Session ID",
                    s.video_name AS "Video Source",
                    e.emp_id AS "Employee ID",
                    e.full_name AS "Full Name",
                    a.action AS "Action",
                    a.timestamp AS "Timestamp"
                FROM actions a
                JOIN sessions s ON a.session_id = s.id
                JOIN employees e ON a.employee_id = e.emp_id
                ORDER BY s.id DESC, a.timestamp ASC
            '''
            return pd.read_sql_query(sql, conn)
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return None

def get_latest_actions(limit=20, session_id=None):
    """Fetches the most recent activity logs for dashboard display."""
    try:
        with get_db_connection() as conn:
            sql = 'SELECT a.*, e.full_name FROM actions a LEFT JOIN employees e ON a.employee_id = e.emp_id'
            if session_id:
                cursor = conn.execute(sql + ' WHERE a.session_id = ? ORDER BY a.timestamp DESC LIMIT ?', (session_id, limit))
            else:
                cursor = conn.execute(sql + ' ORDER BY a.timestamp DESC LIMIT ?', (limit,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching latest actions: {e}")
        return []

def get_all_sessions():
    """Returns a list of all historical sessions."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute('SELECT * FROM sessions ORDER BY start_time DESC')
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        return []
    
def get_session_by_id(session_id):
    """
    Fetches a specific session's details by its ID.
    Returns:
        sqlite3.Row: The session record or None if not found.
    """
    try:
        with get_db_connection() as conn:
            row = conn.execute('SELECT * FROM sessions WHERE id = ?', (session_id,)).fetchone()
            return row
    except Exception as e:
        logger.error(f"Error fetching session {session_id}: {e}")
        return None
    