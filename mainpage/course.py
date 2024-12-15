from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import os
from flask_cors import CORS
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_PATH = 'students.db'  # Path to your SQLite database file
EXCEL_FOLDER = os.path.join(os.getcwd(), 'saved_files')  # Directory to store Excel files
os.makedirs(EXCEL_FOLDER, exist_ok=True)  # Ensure the directory exists

# Connect to the database and create tables
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS header_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    programme TEXT NOT NULL,
    course_name TEXT NOT NULL,
    course_code TEXT NOT NULL,
    academic_year TEXT NOT NULL,
    semester TEXT NOT NULL
)
''')

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


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    return render_template('1stYear.html')


@app.route('/save', methods=['POST'])
def save_data():
    try:
        data = request.json
        header = data.get('header')
        students = data.get('students')

        # Validate incoming data
        if not header or not students:
            return jsonify({'status': 'error', 'message': 'Missing data'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Save header info
        cursor.execute(
            'INSERT INTO header_info (programme, course_name, course_code, academic_year, semester) VALUES (?, ?, ?, ?, ?)',
            (header['programme'], header['courseName'], header['courseCode'], header['academicYear'], header['semester'])
        )
        course_id = cursor.lastrowid

        # Save student data
        for idx, student in enumerate(students, start=1):
            cursor.execute(
                'INSERT INTO student_info (reg_no, name, ese, cia, total, course_id) VALUES (?, ?, ?, ?, ?, ?)',
                (student['regNo'], student['name'], student['ese'], student['cia'], student['total'], course_id)
            )

        conn.commit()

        # Generate Excel file
        filename = f"{header['courseName']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        filepath = os.path.join(EXCEL_FOLDER, filename)

        # Write to Excel file
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Create Header DataFrame
            header_df = pd.DataFrame([header])
            header_df.columns = ["Programme", "Course Name", "Course Code", "Academic Year", "Semester"]

            # Add SN to Students
            for idx, student in enumerate(students, start=1):
                student['SN'] = idx

            # Create Students DataFrame
            student_df = pd.DataFrame(students)
            student_df = student_df[["SN", "regNo", "name", "ese", "cia", "total"]]
            student_df.columns = ["SN", "Reg. No", "Name of the Student", "ESE", "CIA", "Total"]

            # Write to Excel
            header_df.to_excel(writer, sheet_name="Data", index=False, startrow=0)
            student_df.to_excel(writer, sheet_name="Data", index=False, startrow=len(header_df) + 2)

        conn.close()
        return jsonify({'status': 'success', 'filename': filename})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {e}'}), 500


@app.route('/files', methods=['GET'])
def list_files():
    """List all saved Excel files."""
    try:
        files = [f for f in os.listdir(EXCEL_FOLDER) if f.endswith('.xlsx')]
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Serve the requested file."""
    try:
        return send_from_directory(EXCEL_FOLDER, filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404


@app.route('/edit/<filename>', methods=['GET'])
def load_file_for_editing(filename):
    """Load the content of an Excel file for editing."""
    try:
        filepath = os.path.join(EXCEL_FOLDER, filename)

        if not os.path.exists(filepath):
            return jsonify({'status': 'error', 'message': 'File not found'}), 404

        # Read Excel file
        excel_data = pd.read_excel(filepath, sheet_name="Data", engine='openpyxl')

        # Separate header and student data
        header_df = excel_data.iloc[:1].to_dict(orient="records")[0]
        student_df = excel_data.iloc[2:].fillna('').to_dict(orient="records")

        return jsonify({'status': 'success', 'header': header_df, 'students': student_df})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/edit/<filename>', methods=['POST'])
def save_edited_file(filename):
    """Save the edited content back to the Excel file."""
    try:
        data = request.json
        header = data.get('header')
        students = data.get('students')

        # Validate data
        if not header or not students:
            return jsonify({'status': 'error', 'message': 'Missing data'}), 400

        filepath = os.path.join(EXCEL_FOLDER, filename)

        if not os.path.exists(filepath):
            return jsonify({'status': 'error', 'message': 'File not found'}), 404

        # Add SN (reindex student data)
        for idx, student in enumerate(students, start=1):
            student['SN'] = idx

        # Save updated data to Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Create Header DataFrame
            header_df = pd.DataFrame([header])
            header_df.columns = ["Programme", "Course Name", "Course Code", "Academic Year", "Semester"]

            # Create Students DataFrame
            student_df = pd.DataFrame(students)
            student_df = student_df[["SN", "regNo", "name", "ese", "cia", "total"]]
            student_df.columns = ["SN", "Reg. No", "Name of the Student", "ESE", "CIA", "Total"]

            # Write to Excel
            header_df.to_excel(writer, sheet_name="Data", index=False, startrow=0)
            student_df.to_excel(writer, sheet_name="Data", index=False, startrow=len(header_df) + 2)

        return jsonify({'status': 'success', 'message': 'File updated successfully.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        filepath = os.path.join(EXCEL_FOLDER, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'status': 'success', 'message': f'{filename} deleted successfully.'})
        else:
            return jsonify({'status': 'error', 'message': f'{filename} not found.'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
