"""Main Tkinter desktop application."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from threading import Thread
import sqlite3

import database as db
from models import Student, Subject, Attendance
from reports import get_summaries, get_low_attendance
from advanced_python import run_thread_demo, run_process_demo, run_async_demo


class AttendanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        db.initialize_database()

        self.title("Python-Based Attendance Management System")
        self.geometry("1120x720")
        self.minsize(900, 600)

        self.student_map = {}
        self.subject_map = {}

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("AppTitle.TLabel", font=("Arial", 18, "bold"))
        style.configure("Treeview", rowheight=25)

        ttk.Label(
            self,
            text="Python-Based Attendance Management System",
            style="AppTitle.TLabel",
        ).pack(pady=12)

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=8)

        self.dashboard_tab = ttk.Frame(self.tabs, padding=12)
        self.students_tab = ttk.Frame(self.tabs, padding=12)
        self.subjects_tab = ttk.Frame(self.tabs, padding=12)
        self.mark_tab = ttk.Frame(self.tabs, padding=12)
        self.reports_tab = ttk.Frame(self.tabs, padding=12)
        self.history_tab = ttk.Frame(self.tabs, padding=12)
        self.co_tab = ttk.Frame(self.tabs, padding=12)
        self.student_portal_tab = ttk.Frame(self.tabs, padding=12)

        tabs = [
            (self.dashboard_tab, "Dashboard"),
            (self.students_tab, "Students"),
            (self.subjects_tab, "Subjects"),
            (self.mark_tab, "Mark Attendance"),
            (self.reports_tab, "Reports"),
            (self.history_tab, "Attendance History"),
            (self.co_tab, "CO Demonstrations"),
            (self.student_portal_tab, "Student Portal"),
        ]
        for frame, title in tabs:
            self.tabs.add(frame, text=title)

        self.build_dashboard()
        self.build_students()
        self.build_subjects()
        self.build_mark_attendance()
        self.build_reports()
        self.build_history()
        self.build_co_tab()
        self.build_student_portal()
        self.refresh_all()

    def refresh_all(self):
        """Refresh dashboard, student/subject selectors, reports and history."""
        # Student table and selector
        self.student_table.delete(*self.student_table.get_children())
        self.student_map.clear()
        for row in db.get_students():
            self.student_table.insert(
                "", "end",
                values=(row["id"], row["roll_no"], row["name"], row["class_name"]),
            )
            label = f'{row["roll_no"]} - {row["name"]}'
            self.student_map[label] = row["id"]

        # Subject table and selector
        self.subject_table.delete(*self.subject_table.get_children())
        self.subject_map.clear()
        for row in db.get_subjects():
            self.subject_table.insert(
                "", "end", values=(row["id"], row["code"], row["name"]),
            )
            label = f'{row["code"]} - {row["name"]}'
            self.subject_map[label] = row["id"]

        # This screen uses subject_combo; student selection belongs to the Student Portal.
        self.subject_combo["values"] = list(self.subject_map.keys())
        if not self.subject_choice_var.get() and self.subject_map:
            self.subject_choice_var.set(next(iter(self.subject_map)))
        if hasattr(self, "class_attendance_table") and self.subject_choice_var.get() in self.subject_map:
            self.load_class_attendance()

        # Dashboard counters
        counts = db.get_dashboard_counts()
        self.dashboard_info.configure(
            text=(
                f'Students: {counts["students"]}    '
                f'Subjects: {counts["subjects"]}    '
                f'Total attendance records: {counts["attendance"]}    '
                f"Today's records: {counts['today']}"
            )
        )

        self.refresh_reports()
        self.refresh_history()
        if hasattr(self, "portal_student_combo"):
            self.refresh_student_portal_choices()

    # ---------- Reusable table ----------
    def create_table(self, parent, columns, headings, widths):
        wrapper = ttk.Frame(parent)
        wrapper.pack(fill="both", expand=True, pady=8)

        tree = ttk.Treeview(wrapper, columns=columns, show="headings")
        vertical = ttk.Scrollbar(
            wrapper, orient="vertical", command=tree.yview
        )
        horizontal = ttk.Scrollbar(
            wrapper, orient="horizontal", command=tree.xview
        )
        tree.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set,
        )

        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        wrapper.rowconfigure(0, weight=1)
        wrapper.columnconfigure(0, weight=1)

        for index, column in enumerate(columns):
            tree.heading(column, text=headings[index])
            tree.column(column, width=widths[index], anchor="w")

        return tree

    # ---------- Dashboard ----------
    def build_dashboard(self):
        ttk.Label(
            self.dashboard_tab,
            text="System Overview",
            font=("Arial", 15, "bold"),
        ).pack(anchor="w")

        self.dashboard_info = ttk.Label(
            self.dashboard_tab, text="", font=("Arial", 14)
        )
        self.dashboard_info.pack(anchor="w", pady=20)

        ttk.Label(
            self.dashboard_tab,
            text=(
                "Quick start: add students and subjects, mark attendance, "
                "then view attendance percentages and reports."
            ),
            wraplength=950,
        ).pack(anchor="w", pady=5)

        ttk.Label(
            self.dashboard_tab,
            text=(
                "Attendance statuses are Present and Absent. "
                "Records are saved in SQLite and remain after the app closes."
            ),
            wraplength=950,
        ).pack(anchor="w", pady=5)

    # ---------- Student management ----------
    def build_students(self):
        form = ttk.LabelFrame(
            self.students_tab, text="Add Student", padding=10
        )
        form.pack(fill="x")

        self.roll_var = tk.StringVar()
        self.student_name_var = tk.StringVar()
        self.class_var = tk.StringVar(value="BTech CSE")

        fields = [
            ("Roll number", self.roll_var, 15),
            ("Student name", self.student_name_var, 22),
            ("Class / section", self.class_var, 18),
        ]

        for label, variable, width in fields:
            ttk.Label(form, text=label).pack(side="left")
            ttk.Entry(
                form, textvariable=variable, width=width
            ).pack(side="left", padx=5)

        ttk.Button(
            form, text="Add Student", command=self.add_student
        ).pack(side="left", padx=5)
        ttk.Button(
            form, text="Delete Selected", command=self.delete_student
        ).pack(side="left", padx=5)

        self.student_table = self.create_table(
            self.students_tab,
            ("id", "roll", "name", "class_name"),
            ("ID", "Roll Number", "Name", "Class / Section"),
            (60, 140, 250, 200),
        )

    def add_student(self):
        roll = self.roll_var.get().strip()
        name = self.student_name_var.get().strip()
        class_name = self.class_var.get().strip()

        if not roll or not name or not class_name:
            messagebox.showwarning(
                "Missing information", "Fill all student fields."
            )
            return

        student = Student(roll, name, class_name)

        try:
            db.add_student(
                student.roll_no, student.name, student.class_name
            )
            self.roll_var.set("")
            self.student_name_var.set("")
            self.refresh_all()
            messagebox.showinfo("Success", "Student added successfully.")
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate roll number",
                "Each student must have a unique roll number.",
            )

    def delete_student(self):
        selected = self.student_table.selection()
        if not selected:
            messagebox.showwarning(
                "Select student", "Select a student first."
            )
            return

        student_id = self.student_table.item(
            selected[0], "values"
        )[0]

        if messagebox.askyesno(
            "Confirm deletion",
            "Delete this student and their attendance records?",
        ):
            db.delete_student(student_id)
            self.refresh_all()

    # ---------- Subject management ----------
    def build_subjects(self):
        form = ttk.LabelFrame(
            self.subjects_tab, text="Add Subject", padding=10
        )
        form.pack(fill="x")

        self.subject_code_var = tk.StringVar()
        self.subject_name_var = tk.StringVar()

        ttk.Label(form, text="Subject code").pack(side="left")
        ttk.Entry(
            form, textvariable=self.subject_code_var, width=15
        ).pack(side="left", padx=5)

        ttk.Label(form, text="Subject name").pack(side="left")
        ttk.Entry(
            form, textvariable=self.subject_name_var, width=25
        ).pack(side="left", padx=5)

        ttk.Button(
            form, text="Add Subject", command=self.add_subject
        ).pack(side="left", padx=5)
        ttk.Button(
            form, text="Delete Selected", command=self.delete_subject
        ).pack(side="left", padx=5)

        self.subject_table = self.create_table(
            self.subjects_tab,
            ("id", "code", "name"),
            ("ID", "Subject Code", "Subject Name"),
            (60, 160, 350),
        )

    def add_subject(self):
        code = self.subject_code_var.get().strip()
        name = self.subject_name_var.get().strip()

        if not code or not name:
            messagebox.showwarning(
                "Missing information", "Enter both subject code and name."
            )
            return

        subject = Subject(code, name)

        try:
            db.add_subject(subject.code, subject.name)
            self.subject_code_var.set("")
            self.subject_name_var.set("")
            self.refresh_all()
            messagebox.showinfo("Success", "Subject added successfully.")
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate subject code",
                "Each subject must have a unique code.",
            )

    def delete_subject(self):
        selected = self.subject_table.selection()
        if not selected:
            messagebox.showwarning(
                "Select subject", "Select a subject first."
            )
            return

        subject_id = self.subject_table.item(
            selected[0], "values"
        )[0]

        if messagebox.askyesno(
            "Confirm deletion",
            "Delete this subject and its attendance records?",
        ):
            db.delete_subject(subject_id)
            self.refresh_all()

    # ---------- Attendance entry ----------
    def build_mark_attendance(self):
        controls = ttk.LabelFrame(self.mark_tab, text="Class Attendance", padding=12)
        controls.pack(fill="x", pady=(0, 10))

        self.subject_choice_var = tk.StringVar()
        self.attendance_date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Label(controls, text="Subject").grid(row=0, column=0, padx=5, pady=6, sticky="w")
        self.subject_combo = ttk.Combobox(controls, textvariable=self.subject_choice_var, state="readonly", width=32)
        self.subject_combo.grid(row=0, column=1, padx=5, pady=6, sticky="w")
        self.subject_combo.bind("<<ComboboxSelected>>", lambda _event: self.load_class_attendance())
        ttk.Label(controls, text="Date (YYYY-MM-DD)").grid(row=0, column=2, padx=5, pady=6, sticky="w")
        date_entry = ttk.Entry(controls, textvariable=self.attendance_date_var, width=15)
        date_entry.grid(row=0, column=3, padx=5, pady=6, sticky="w")
        ttk.Button(controls, text="Load Students", command=self.load_class_attendance).grid(row=0, column=4, padx=8, pady=6)

        actions = ttk.Frame(self.mark_tab)
        actions.pack(fill="x", pady=(0, 8))
        ttk.Button(actions, text="Set All Present", command=lambda: self.set_all_attendance("Present")).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Set All Absent", command=lambda: self.set_all_attendance("Absent")).pack(side="left", padx=6)
        ttk.Button(actions, text="Toggle Selected", command=self.toggle_selected_attendance).pack(side="left", padx=6)
        ttk.Button(actions, text="Save Attendance for All Students", command=self.save_class_attendance).pack(side="right")

        self.class_attendance_table = self.create_table(
            self.mark_tab,
            ("roll", "student", "class", "status"),
            ("Roll Number", "Student Name", "Class", "Status (double-click to change)"),
            (130, 260, 180, 220),
        )
        self.class_attendance_table.bind("<Double-1>", self.toggle_selected_attendance_event)
        self.class_attendance_rows = {}
        ttk.Label(self.mark_tab, text="Choose a subject and date. Double-click a student row to switch Present/Absent, or use the bulk buttons, then save.").pack(anchor="w", pady=8)

    def load_class_attendance(self):
        self.class_attendance_table.delete(*self.class_attendance_table.get_children())
        self.class_attendance_rows = {}
        subject_id = self.subject_map.get(self.subject_choice_var.get())
        day = self.attendance_date_var.get().strip()
        if subject_id is None:
            return
        try:
            date.fromisoformat(day)
        except ValueError:
            messagebox.showerror("Invalid date", "Enter the date as YYYY-MM-DD.")
            return
        existing = {}
        with db.connect() as connection:
            rows = connection.execute(
                "SELECT student_id, status FROM attendance WHERE subject_id = ? AND attendance_date = ?",
                (subject_id, day),
            ).fetchall()
            existing = {row["student_id"]: row["status"] for row in rows}
        for student in db.get_students():
            status = existing.get(student["id"], "Present")
            iid = str(student["id"])
            self.class_attendance_rows[iid] = {"student_id": student["id"], "status": status}
            self.class_attendance_table.insert("", "end", iid=iid, values=(student["roll_no"], student["name"], student["class_name"], status))

    def set_all_attendance(self, status):
        for iid, row in self.class_attendance_rows.items():
            row["status"] = status
            values = list(self.class_attendance_table.item(iid, "values"))
            values[3] = status
            self.class_attendance_table.item(iid, values=values)

    def toggle_selected_attendance_event(self, _event=None):
        self.toggle_selected_attendance()

    def toggle_selected_attendance(self):
        selected = self.class_attendance_table.selection()
        if not selected:
            messagebox.showwarning("Select student", "Select a student row first.")
            return
        for iid in selected:
            new_status = "Absent" if self.class_attendance_rows[iid]["status"] == "Present" else "Present"
            self.class_attendance_rows[iid]["status"] = new_status
            values = list(self.class_attendance_table.item(iid, "values"))
            values[3] = new_status
            self.class_attendance_table.item(iid, values=values)

    def save_class_attendance(self):
        subject_id = self.subject_map.get(self.subject_choice_var.get())
        day = self.attendance_date_var.get().strip()
        if subject_id is None:
            messagebox.showwarning("Select subject", "Please select a subject first.")
            return
        try:
            date.fromisoformat(day)
        except ValueError:
            messagebox.showerror("Invalid date", "Enter the date as YYYY-MM-DD.")
            return
        if not self.class_attendance_rows:
            self.load_class_attendance()
        if not self.class_attendance_rows:
            messagebox.showwarning("No students", "Add students before taking attendance.")
            return
        try:
            for row in self.class_attendance_rows.values():
                db.save_attendance(row["student_id"], subject_id, day, row["status"])
            self.refresh_all()
            self.load_class_attendance()
            messagebox.showinfo("Saved", f"Attendance saved for {len(self.class_attendance_rows)} students.")
        except (sqlite3.Error, ValueError) as error:
            messagebox.showerror("Save failed", str(error))

    # ---------- Reports ----------
    def build_reports(self):
        toolbar = ttk.Frame(self.reports_tab)
        toolbar.pack(fill="x")

        ttk.Button(
            toolbar, text="Refresh Reports",
            command=self.refresh_reports,
        ).pack(side="left")
        ttk.Button(
            toolbar, text="Show Below 75%",
            command=self.show_low_attendance,
        ).pack(side="left", padx=6)
        ttk.Button(
            toolbar, text="Show Chart",
            command=self.show_chart,
        ).pack(side="left", padx=6)

        self.report_table = self.create_table(
            self.reports_tab,
            ("roll", "student", "subject", "total", "present", "percent"),
            ("Roll Number", "Student", "Subject", "Classes", "Present", "Attendance %"),
            (110, 180, 240, 90, 90, 120),
        )

    def refresh_reports(self, rows=None):
        self.report_table.delete(
            *self.report_table.get_children()
        )

        if rows is None:
            rows = get_summaries()

        for row in rows:
            percentage = row["percentage"] or 0
            self.report_table.insert(
                "", "end",
                values=(
                    row["roll_no"],
                    row["student_name"],
                    row["subject_code"] + " - " + row["subject_name"],
                    row["total_classes"],
                    row["present_count"] or 0,
                    f"{percentage:.1f}%",
                ),
            )

    def show_low_attendance(self):
        self.refresh_reports(get_low_attendance(75))


    def show_chart(self):
        rows = [
            row for row in get_summaries()
            if row["total_classes"] > 0
        ]

        if not rows:
            messagebox.showinfo(
                "No data", "Mark attendance before creating a chart."
            )
            return

        try:
            import matplotlib.pyplot as plt
        except ImportError:
            messagebox.showerror(
                "Library missing",
                "Install Matplotlib with: pip install matplotlib",
            )
            return

        labels = [
            row["roll_no"] + "/" + row["subject_code"] for row in rows
        ]
        values = [row["percentage"] or 0 for row in rows]

        plt.figure(figsize=(9, 4))
        plt.bar(labels, values)
        plt.axhline(75, linestyle="--", label="75% threshold")
        plt.ylabel("Attendance percentage")
        plt.title("Attendance by Student and Subject")
        plt.ylim(0, 105)
        plt.xticks(rotation=45, ha="right")
        plt.legend()
        plt.tight_layout()
        plt.show()

    # ---------- Attendance history ----------
    def build_history(self):
        toolbar = ttk.Frame(self.history_tab)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Refresh History", command=self.refresh_history).pack(side="left")
        ttk.Button(toolbar, text="Delete Selected Record", command=self.delete_selected_record).pack(side="left", padx=10)
        self.history_table = self.create_table(
            self.history_tab,
            ("roll", "student", "class", "code", "subject", "day", "status"),
            ("Roll Number", "Student", "Class", "Code", "Subject", "Date", "Status"),
            (100, 160, 130, 90, 180, 120, 100),
        )

    def refresh_history(self):
        self.history_table.delete(*self.history_table.get_children())
        for row in db.get_attendance_records():
            self.history_table.insert("", "end", iid=str(row["attendance_id"]), values=(
                row["roll_no"], row["student_name"], row["class_name"], row["subject_code"],
                row["subject_name"], row["attendance_date"], row["status"],
            ))

    def delete_selected_record(self):
        selected = self.history_table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an attendance record first.")
            return
        if not messagebox.askyesno("Confirm deletion", "Delete the selected attendance record?"):
            return
        try:
            db.delete_attendance_record(int(selected[0]))
            self.refresh_all()
            self.refresh_history()
            messagebox.showinfo("Deleted", "Attendance record deleted.")
        except sqlite3.Error as error:
            messagebox.showerror("Delete failed", str(error))

    # ---------- CO1-CO5 demonstrations ----------
    # ---------- Student portal (local demonstration) ----------
    def build_student_portal(self):
        """Display a selected student's attendance summary, history and graph."""
        intro = ttk.Label(
            self.student_portal_tab,
            text="Student Attendance Portal — choose a student to view their attendance.",
            font=("Arial", 12, "bold"),
        )
        intro.pack(anchor="w", pady=(0, 10))

        controls = ttk.Frame(self.student_portal_tab)
        controls.pack(fill="x", pady=(0, 8))
        ttk.Label(controls, text="Student:").pack(side="left", padx=(0, 6))
        self.portal_student_var = tk.StringVar()
        self.portal_student_combo = ttk.Combobox(
            controls, textvariable=self.portal_student_var,
            state="readonly", width=35,
        )
        self.portal_student_combo.pack(side="left", padx=(0, 8))
        self.portal_student_combo.bind(
            "<<ComboboxSelected>>", lambda _event: self.refresh_student_portal()
        )
        ttk.Button(
            controls, text="View My Attendance", command=self.refresh_student_portal
        ).pack(side="left")

        self.portal_summary_label = ttk.Label(
            self.student_portal_tab, text="Select a student to view attendance.",
            font=("Arial", 11),
        )
        self.portal_summary_label.pack(anchor="w", pady=6)

        body = ttk.Panedwindow(self.student_portal_tab, orient="horizontal")
        body.pack(fill="both", expand=True, pady=6)
        left = ttk.Frame(body, padding=4)
        right = ttk.LabelFrame(body, text="Subject-wise attendance graph", padding=8)
        body.add(left, weight=3)
        body.add(right, weight=2)

        self.portal_table = self.create_table(
            left,
            ("subject", "total", "present", "absent", "percentage", "warning"),
            ("Subject", "Classes", "Present", "Absent", "Attendance %", "Status"),
            (190, 65, 65, 65, 105, 130),
        )
        self.portal_chart = tk.Canvas(right, height=300, background="white", highlightthickness=0)
        self.portal_chart.pack(fill="both", expand=True)
        self.portal_chart.bind("<Configure>", lambda _event: self.refresh_student_portal())
        self.portal_student_ids = {}

    def refresh_student_portal_choices(self):
        if not hasattr(self, "portal_student_combo"):
            return
        students = db.get_students()
        labels = [f'{row["roll_no"]} - {row["name"]}' for row in students]
        self.portal_student_ids = {
            f'{row["roll_no"]} - {row["name"]}': row["id"] for row in students
        }
        current = self.portal_student_var.get()
        self.portal_student_combo["values"] = labels
        if current not in self.portal_student_ids and labels:
            self.portal_student_var.set(labels[0])
        elif not labels:
            self.portal_student_var.set("")
        self.refresh_student_portal()

    def refresh_student_portal(self):
        if not hasattr(self, "portal_table"):
            return
        self.portal_table.delete(*self.portal_table.get_children())
        self.portal_chart.delete("all")
        student_id = self.portal_student_ids.get(self.portal_student_var.get())
        if student_id is None:
            self.portal_summary_label.configure(text="No students available. Add a student first.")
            return

        summaries = []
        with db.connect() as connection:
            rows = connection.execute(
                """SELECT sub.code, sub.name, COUNT(a.id) AS total_classes,
                          COALESCE(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END),0) AS present_count,
                          COALESCE(SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END),0) AS absent_count
                   FROM subjects sub
                   LEFT JOIN attendance a ON a.subject_id=sub.id AND a.student_id=?
                   GROUP BY sub.id ORDER BY sub.code""",
                (student_id,),
            ).fetchall()
            history = connection.execute(
                """SELECT sub.code, sub.name, a.attendance_date, a.status
                   FROM attendance a JOIN subjects sub ON sub.id=a.subject_id
                   WHERE a.student_id=? ORDER BY a.attendance_date DESC, sub.code""",
                (student_id,),
            ).fetchall()

        total = present = 0
        for row in rows:
            total += row["total_classes"]
            present += row["present_count"]
            percent = (100.0 * row["present_count"] / row["total_classes"]) if row["total_classes"] else 0.0
            item = {
                "label": f'{row["code"]} - {row["name"]}',
                "total": row["total_classes"],
                "present": row["present_count"],
                "absent": row["absent_count"],
                "percentage": percent,
            }
            summaries.append(item)
            warning = "Below 75%" if row["total_classes"] and percent < 75 else ("No records" if not row["total_classes"] else "OK")
            self.portal_table.insert("", "end", values=(item["label"], item["total"], item["present"], item["absent"], f"{percent:.1f}%", warning))

        overall = (100.0 * present / total) if total else 0.0
        absent = total - present
        self.portal_summary_label.configure(
            text=f"Overall attendance: {overall:.1f}%    |    Classes recorded: {total}    |    Present: {present}    |    Absent: {absent}"
        )
        self._draw_student_portal_chart(summaries)

    def _draw_student_portal_chart(self, summaries):
        canvas = self.portal_chart
        canvas.delete("all")
        width = max(canvas.winfo_width(), 300)
        height = max(canvas.winfo_height(), 220)
        if not summaries:
            canvas.create_text(width / 2, height / 2, text="No subjects available", fill="#444")
            return
        canvas.create_text(12, 12, anchor="nw", text="Attendance percentage (75% target)", fill="#222")
        bar_top = 42
        row_height = max(34, min(52, (height - bar_top - 12) // len(summaries)))
        label_width = min(135, width * 0.42)
        graph_width = max(70, width - label_width - 38)
        for index, item in enumerate(summaries):
            y = bar_top + index * row_height
            if y + row_height > height:
                break
            label = item["label"].split(" - ")[0]
            canvas.create_text(8, y + 10, anchor="nw", text=label, fill="#222")
            x0 = label_width
            x1 = x0 + graph_width
            canvas.create_rectangle(x0, y + 5, x1, y + 21, outline="#bbb", fill="#eee")
            percent = max(0, min(100, item["percentage"]))
            canvas.create_rectangle(x0, y + 5, x0 + graph_width * percent / 100, y + 21, outline="", fill="#4b8fbd")
            target_x = x0 + graph_width * 0.75
            canvas.create_line(target_x, y + 1, target_x, y + 25, fill="#c0392b", width=2)
            canvas.create_text(x1 + 4, y + 4, anchor="nw", text=f"{percent:.0f}%", fill="#222")

    def build_co_tab(self):
        descriptions = [
            ("CO1 — OOP", "models.py contains User, Student, Faculty, Subject and Attendance classes. Student and Faculty inherit from User."),
            ("CO2 — Functional style", "reports.py uses reusable functions, list comprehensions and filtering to process attendance records."),
            ("CO3 — Concurrency", "Run the threading, multiprocessing and asyncio demonstrations below."),
            ("CO4 — Data handling and visualization", "Reports support pandas when installed, CSV export, and a Matplotlib chart."),
            ("CO5 — Full application", "Tkinter interface, Python logic and SQLite database work together offline."),
        ]

        for heading, description in descriptions:
            box = ttk.LabelFrame(
                self.co_tab, text=heading, padding=8
            )
            box.pack(fill="x", pady=4)
            ttk.Label(
                box, text=description, wraplength=950
            ).pack(anchor="w")

        buttons = ttk.Frame(self.co_tab)
        buttons.pack(fill="x", pady=8)

        ttk.Button(
            buttons, text="Threading Demo",
            command=self.threading_demo,
        ).pack(side="left")
        ttk.Button(
            buttons, text="Multiprocessing Demo",
            command=self.multiprocessing_demo,
        ).pack(side="left", padx=6)
        ttk.Button(
            buttons, text="Asyncio Demo",
            command=self.asyncio_demo,
        ).pack(side="left")

        self.co_output = tk.Text(
            self.co_tab, height=7, wrap="word"
        )
        self.co_output.pack(fill="both", expand=True, pady=8)
        self.co_output.insert("end", "Click a button to run a CO3 demonstration.\n")
        self.co_output.configure(state="disabled")

    def show_co_output(self, message):
        def update_text():
            self.co_output.configure(state="normal")
            self.co_output.insert("end", message + "\n")
            self.co_output.see("end")
            self.co_output.configure(state="disabled")

        self.after(0, update_text)

    def threading_demo(self):
        run_thread_demo(self.show_co_output)
        self.show_co_output("Started background thread...")

    def multiprocessing_demo(self):
        statuses = [
            row["status"] for row in db.get_attendance_records()
        ]

        def worker():
            try:
                result = run_process_demo(statuses)
                self.show_co_output(
                    f"Multiprocessing result: {result}"
                )
            except Exception as error:
                self.show_co_output(
                    f"Multiprocessing demo error: {error}"
                )

        Thread(target=worker, daemon=True).start()
        self.show_co_output("Started separate-process calculation...")

    def asyncio_demo(self):
        run_async_demo(self.show_co_output)
        self.show_co_output("Started asyncio demonstration...")


if __name__ == "__main__":
    app = AttendanceApp()
    app.mainloop()
