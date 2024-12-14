from flask import Flask, request, jsonify, render_template
import sqlite3
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = 'students.db'  # Path to your SQLite database file

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create the `header_info` table
cursor.execute('''
CREATE TABLE IF NOT EXISTS header_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name TEXT NOT NULL,
    course_code TEXT NOT NULL,
    academic_year TEXT NOT NULL,
    semester TEXT NOT NULL
)
''')

# Create the `student_info` table
cursor.execute('''
CREATE TABLE IF NOT EXISTS student_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reg_no TEXT NOT NULL,
    name TEXT NOT NULL,
    ese INTEGER NOT NULL,
    cia INTEGER NOT NULL,
    total INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    FOREIGN KEY (course_id) REFERENCES header_info (id)
)
''')

conn.commit()
conn.close()
print("Tables created successfully.")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'students.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('1stYear.html')

@app.route('/save', methods=['POST'])
def save_data():
    data = request.json
    header = data['header']
    students = data['students']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Save header info
    cursor.execute(
        'INSERT INTO header_info (course_name, course_code, academic_year, semester) VALUES (?, ?, ?, ?)',
        (header['courseName'], header['courseCode'], header['academicYear'], header['semester'])
    )
    course_id = cursor.lastrowid

    # Save students data
    for student in students:
        cursor.execute(
            'INSERT INTO student_info (reg_no, name, ese, cia, total, course_id) VALUES (?, ?, ?, ?, ?, ?)',
            (student['regNo'], student['name'], student['ese'], student['cia'], student['total'], course_id)
        )

    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/get/<int:course_id>', methods=['GET'])
def get_data(course_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get header info
    header = cursor.execute(
        'SELECT * FROM header_info WHERE id = ?', (course_id,)
    ).fetchone()

    if not header:
        conn.close()
        return jsonify({'error': 'Course not found'}), 404

    # Get students info
    students = cursor.execute(
        'SELECT * FROM student_info WHERE course_id = ?', (course_id,)
    ).fetchall()

    conn.close()
    return jsonify({
        'header': dict(header),
        'students': [dict(student) for student in students]
    })

if __name__ == '__main__':
    app.run(debug=True)
