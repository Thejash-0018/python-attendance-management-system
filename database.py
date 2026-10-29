"""Database setup and CRUD operations for Attendance Management System."""
import sqlite3
from pathlib import Path
from datetime import date

DB_PATH = Path(__file__).with_name("attendance.db")


def connect():
    """Create a database connection with foreign-key enforcement."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Create required tables and insert sample records on first run."""
    with connect() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                class_name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                attendance_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
                UNIQUE(student_id, subject_id, attendance_date),
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
            );
        """)

        student_count = connection.execute(
            "SELECT COUNT(*) FROM students"
        ).fetchone()[0]

        if student_count == 0:
            connection.executemany(
                "INSERT INTO students(roll_no, name, class_name) VALUES (?, ?, ?)",
                [
                    ("CSE001", "Aarav Kumar", "BTech CSE"),
                    ("CSE002", "Priya Reddy", "BTech CSE"),
                    ("CSE003", "Rahul Sharma", "BTech CSE"),
                ],
            )

        subject_count = connection.execute(
            "SELECT COUNT(*) FROM subjects"
        ).fetchone()[0]

        if subject_count == 0:
            connection.executemany(
                "INSERT INTO subjects(code, name) VALUES (?, ?)",
                [
                    ("CS301", "Python Programming"),
                    ("CS302", "Database Systems"),
                ],
            )


def get_students():
    with connect() as connection:
        return connection.execute(
            "SELECT * FROM students ORDER BY roll_no"
        ).fetchall()


def add_student(roll_no, name, class_name):
    with connect() as connection:
        connection.execute(
            "INSERT INTO students(roll_no, name, class_name) VALUES (?, ?, ?)",
            (roll_no.strip(), name.strip(), class_name.strip()),
        )


def delete_student(student_id):
    with connect() as connection:
        connection.execute(
            "DELETE FROM students WHERE id = ?", (student_id,)
        )


def get_subjects():
    with connect() as connection:
        return connection.execute(
            "SELECT * FROM subjects ORDER BY code"
        ).fetchall()


def add_subject(code, name):
    with connect() as connection:
        connection.execute(
            "INSERT INTO subjects(code, name) VALUES (?, ?)",
            (code.strip(), name.strip()),
        )


def delete_subject(subject_id):
    with connect() as connection:
        connection.execute(
            "DELETE FROM subjects WHERE id = ?", (subject_id,)
        )


def save_attendance(student_id, subject_id, attendance_date, status):
    """Insert attendance or update it if the same student/date/subject exists."""
    if status not in ("Present", "Absent"):
        raise ValueError("Attendance status must be Present or Absent.")

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO attendance
                (student_id, subject_id, attendance_date, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(student_id, subject_id, attendance_date)
            DO UPDATE SET status = excluded.status
            """,
            (student_id, subject_id, attendance_date, status),
        )


def get_attendance_records():
    with connect() as connection:
        return connection.execute(
            """
            SELECT a.id AS attendance_id, s.roll_no, s.name AS student_name, s.class_name,
                   sub.code AS subject_code, sub.name AS subject_name,
                   a.attendance_date, a.status
            FROM attendance AS a
            JOIN students AS s ON s.id = a.student_id
            JOIN subjects AS sub ON sub.id = a.subject_id
            ORDER BY a.attendance_date DESC, s.roll_no
            """
        ).fetchall()


def get_attendance_summary():
    with connect() as connection:
        return connection.execute(
            """
            SELECT s.roll_no, s.name AS student_name,
                   sub.code AS subject_code, sub.name AS subject_name,
                   COUNT(a.id) AS total_classes,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
                   ROUND(
                       100.0 * SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END)
                       / NULLIF(COUNT(a.id), 0), 1
                   ) AS percentage
            FROM students AS s
            CROSS JOIN subjects AS sub
            LEFT JOIN attendance AS a
                ON a.student_id = s.id AND a.subject_id = sub.id
            GROUP BY s.id, sub.id
            ORDER BY s.roll_no, sub.code
            """
        ).fetchall()


def get_dashboard_counts():
    today = date.today().isoformat()
    with connect() as connection:
        student_count = connection.execute(
            "SELECT COUNT(*) FROM students"
        ).fetchone()[0]
        subject_count = connection.execute(
            "SELECT COUNT(*) FROM subjects"
        ).fetchone()[0]
        attendance_count = connection.execute(
            "SELECT COUNT(*) FROM attendance"
        ).fetchone()[0]
        today_count = connection.execute(
            "SELECT COUNT(*) FROM attendance WHERE attendance_date = ?",
            (today,),
        ).fetchone()[0]

    return {
        "students": student_count,
        "subjects": subject_count,
        "attendance": attendance_count,
        "today": today_count,
    }


def delete_attendance_record(attendance_id):
    """Delete one attendance row by its database ID."""
    with connect() as connection:
        connection.execute("DELETE FROM attendance WHERE id = ?", (attendance_id,))


def get_student_attendance_summary(student_id):
    """Return subject-wise attendance totals for one student."""
    with connect() as connection:
        return connection.execute(
            """
            SELECT sub.code AS subject_code, sub.name AS subject_name,
                   COUNT(a.id) AS total_classes,
                   COALESCE(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END), 0) AS present_count,
                   COALESCE(SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END), 0) AS absent_count,
                   ROUND(100.0 * SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END)
                         / NULLIF(COUNT(a.id), 0), 1) AS percentage
            FROM subjects AS sub
            LEFT JOIN attendance AS a
                ON a.subject_id = sub.id AND a.student_id = ?
            GROUP BY sub.id
            ORDER BY sub.code
            """, (student_id,)
        ).fetchall()


def get_student_attendance_history(student_id, limit=100):
    """Return recent attendance records for one student."""
    with connect() as connection:
        return connection.execute(
            """
            SELECT a.attendance_date, a.status, sub.code AS subject_code, sub.name AS subject_name
            FROM attendance AS a
            JOIN subjects AS sub ON sub.id = a.subject_id
            WHERE a.student_id = ?
            ORDER BY a.attendance_date DESC, sub.code
            LIMIT ?
            """, (student_id, limit)
        ).fetchall()
