import sqlite3
import datetime

def connect_db():
    """Creates or connects to the database and returns the connection."""
    conn = sqlite3.connect('school.db')
    conn.execute("PRAGMA foreign_keys = 1") # Enforce foreign keys
    return conn

def setup_database():
    """Creates or updates the database schema."""
    conn = connect_db()
    cursor = conn.cursor()
    
    # --- 1. Create Students Table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        date_of_birth TEXT,
        place_of_birth TEXT,
        class_into_which_admission_is_sought TEXT,
        last_school_attended TEXT,
        reason_for_leaving_last_school TEXT,
        father_name TEXT,
        father_occupation TEXT,
        father_office_address TEXT,
        mother_name TEXT,
        mother_occupation TEXT,
        mother_office_address TEXT,
        guardian_name TEXT,
        residential_address TEXT,
        contact_details TEXT,
        brothers_sisters_applicant TEXT,
        medical_info TEXT,
        admission_date TEXT,
        status TEXT DEFAULT 'Active',
        photo_path TEXT 
    )
    """)
    
    # --- 2. Rename old 'fees' table if exists ---
    try:
        cursor.execute("ALTER TABLE fees RENAME TO fees_old")
    except sqlite3.OperationalError:
        pass 

    # --- 3. Create new 'challans' table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS challans (
        challan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        issue_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        status TEXT DEFAULT 'Unpaid',
        payment_date TEXT,
        total_amount REAL DEFAULT 0,
        arrears REAL DEFAULT 0,
        fine REAL DEFAULT 0,
        FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE
    )
    """)

    # --- 4. Create new 'challan_items' table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS challan_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        challan_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        FOREIGN KEY (challan_id) REFERENCES challans (challan_id) ON DELETE CASCADE
    )
    """)
    
    # --- 5. Create Users Table for Login ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    
    # Create Default Admin User if none exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'admin'))
        print("Default user 'admin' created with password 'admin'.")

    # Add photo_path if missing (Legacy check)
    try:
        cursor.execute("ALTER TABLE students ADD COLUMN photo_path TEXT")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()
    print("Database and tables created successfully.")

# === LOGIN FUNCTIONS ===

def check_login(username, password):
    """Verifies username and password."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def update_password(username, new_password):
    """Updates the password for a specific user."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
    conn.commit()
    conn.close()
    return True

# === STUDENT FUNCTIONS ===

def add_student(full_name, date_of_birth, place_of_birth, class_into_which_admission_is_sought,
                last_school_attended, reason_for_leaving_last_school, father_name, father_occupation,
                father_office_address, mother_name, mother_occupation, mother_office_address,
                guardian_name, residential_address, contact_details, brothers_sisters_applicant,
                medical_info, admission_date, status, photo_path):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO students (
            full_name, date_of_birth, place_of_birth, class_into_which_admission_is_sought,
            last_school_attended, reason_for_leaving_last_school, father_name, father_occupation,
            father_office_address, mother_name, mother_occupation, mother_office_address,
            guardian_name, residential_address, contact_details, brothers_sisters_applicant,
            medical_info, admission_date, status, photo_path
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        full_name, date_of_birth, place_of_birth, class_into_which_admission_is_sought,
        last_school_attended, reason_for_leaving_last_school, father_name, father_occupation,
        father_office_address, mother_name, mother_occupation, mother_office_address,
        guardian_name, residential_address, contact_details, brothers_sisters_applicant,
        medical_info, admission_date, status, photo_path
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_student(student_id, full_name, date_of_birth, place_of_birth, class_into_which_admission_is_sought,
                   last_school_attended, reason_for_leaving_last_school, father_name, father_occupation,
                   father_office_address, mother_name, mother_occupation, mother_office_address,
                   guardian_name, residential_address, contact_details, brothers_sisters_applicant,
                   medical_info, admission_date, status, photo_path):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students SET 
            full_name=?, date_of_birth=?, place_of_birth=?, class_into_which_admission_is_sought=?,
            last_school_attended=?, reason_for_leaving_last_school=?, father_name=?, father_occupation=?,
            father_office_address=?, mother_name=?, mother_occupation=?, mother_office_address=?,
            guardian_name=?, residential_address=?, contact_details=?, brothers_sisters_applicant=?,
            medical_info=?, admission_date=?, status=?, photo_path=?
        WHERE student_id=?
    """, (
        full_name, date_of_birth, place_of_birth, class_into_which_admission_is_sought,
        last_school_attended, reason_for_leaving_last_school, father_name, father_occupation,
        father_office_address, mother_name, mother_occupation, mother_office_address,
        guardian_name, residential_address, contact_details, brothers_sisters_applicant,
        medical_info, admission_date, status, photo_path, student_id
    ))
    conn.commit()
    conn.close()

def get_students(search_term=""):
    conn = connect_db()
    cursor = conn.cursor()
    if search_term:
        cursor.execute("SELECT * FROM students WHERE full_name LIKE ?", ('%' + search_term + '%',))
    else:
        cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    conn.close()
    return students

def get_active_students():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE status = 'Active'")
    students = cursor.fetchall()
    conn.close()
    return students

def get_student_by_id(student_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    student = cursor.fetchone()
    conn.close()
    return student

def delete_student(student_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
    try:
        cursor.execute("DELETE FROM fees_old WHERE student_id = ?", (student_id,))
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

# === CHALLAN & FEE FUNCTIONS ===

def create_challan(student_id, issue_date, due_date, status, items, arrears=0, fine=0):
    conn = connect_db()
    cursor = conn.cursor()
    total_amount = sum(item[1] for item in items) + arrears + fine
    
    cursor.execute("""
        INSERT INTO challans (student_id, issue_date, due_date, status, total_amount, arrears, fine)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (student_id, issue_date, due_date, status, total_amount, arrears, fine))
    challan_id = cursor.lastrowid
    
    for desc, amount in items:
        cursor.execute("""
            INSERT INTO challan_items (challan_id, description, amount)
            VALUES (?, ?, ?)
        """, (challan_id, desc, amount))
    conn.commit()
    conn.close()
    return challan_id

def get_challans_by_student_id(student_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM challans WHERE student_id = ? ORDER BY issue_date DESC", (student_id,))
    challans = cursor.fetchall()
    conn.close()
    return challans

def get_challan_details_by_id(challan_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM challans WHERE challan_id = ?", (challan_id,))
    challan = cursor.fetchone()
    cursor.execute("SELECT description, amount FROM challan_items WHERE challan_id = ?", (challan_id,))
    items = cursor.fetchall()
    conn.close()
    return challan, items

def get_unpaid_challans(student_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM challans WHERE student_id = ? AND status = 'Unpaid'", (student_id,))
    unpaid_challans = cursor.fetchall()
    conn.close()
    return unpaid_challans

def pay_challan(challan_id, payment_date):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE challans SET status = 'Paid', payment_date = ?
        WHERE challan_id = ?
    """, (payment_date, challan_id))
    conn.commit()
    conn.close()

# === REPORTING FUNCTIONS ===

def get_student_fee_summary():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.student_id, s.full_name, s.class_into_which_admission_is_sought, s.contact_details,
        SUM(CASE WHEN c.status = 'Unpaid' THEN c.total_amount ELSE 0 END) as total_due
        FROM students s LEFT JOIN challans c ON s.student_id = c.student_id
        WHERE s.status = 'Active' GROUP BY s.student_id ORDER BY total_due DESC
    """)
    summary = cursor.fetchall()
    conn.close()
    return summary

def get_classwise_defaulter_list():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.class_into_which_admission_is_sought, s.full_name, SUM(c.total_amount) as total_due
        FROM students s JOIN challans c ON s.student_id = c.student_id
        WHERE c.status = 'Unpaid' AND s.status = 'Active'
        GROUP BY s.class_into_which_admission_is_sought, s.full_name
        HAVING total_due > 0 ORDER BY s.class_into_which_admission_is_sought, s.full_name
    """)
    defaulters = cursor.fetchall()
    conn.close()
    class_map = {}
    for s_class, name, due in defaulters:
        if s_class not in class_map: class_map[s_class] = []
        class_map[s_class].append((name, due))
    return class_map

def get_classwise_posting_sheet(month, year):
    conn = connect_db()
    cursor = conn.cursor()
    month_str = f"{month:02d}"
    cursor.execute(f"""
        SELECT s.class_into_which_admission_is_sought, s.full_name, c.challan_id, c.payment_date, c.total_amount, c.arrears, c.fine
        FROM challans c JOIN students s ON s.student_id = c.student_id
        WHERE c.status = 'Paid' AND strftime('%Y', c.payment_date) = ? AND strftime('%m', c.payment_date) = ?
        ORDER BY s.class_into_which_admission_is_sought, s.full_name
    """, (str(year), month_str))
    postings = cursor.fetchall()
    conn.close()
    class_map = {}
    for row in postings:
        s_class = row[0]
        if s_class not in class_map: class_map[s_class] = []
        class_map[s_class].append(row[1:])
    return class_map

def get_collection_summary(start_date, end_date):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT payment_date, COUNT(challan_id), SUM(total_amount) FROM challans
        WHERE status = 'Paid' AND payment_date BETWEEN ? AND ?
        GROUP BY payment_date ORDER BY payment_date
    """, (start_date, end_date))
    summary = cursor.fetchall()
    conn.close()
    return summary

def get_new_admissions_list(start_date, end_date):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT admission_date, full_name, class_into_which_admission_is_sought, father_name, contact_details
        FROM students WHERE admission_date BETWEEN ? AND ? ORDER BY admission_date
    """, (start_date, end_date))
    admissions = cursor.fetchall()
    conn.close()
    return admissions

def get_struck_off_list():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT full_name, class_into_which_admission_is_sought, father_name, contact_details, status
        FROM students WHERE status = 'Withdrawn' OR status = 'Inactive' ORDER BY full_name
    """)
    struck_off = cursor.fetchall()
    conn.close()
    return struck_off

if __name__ == "__main__":
    setup_database()