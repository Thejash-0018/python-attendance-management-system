"""Object-oriented model classes for CO1."""


class User:
    """Base class for people who use the system."""

    def __init__(self, name):
        self.name = name


class Student(User):
    """Student inherits common user information."""

    def __init__(self, roll_no, name, class_name):
        super().__init__(name)
        self.roll_no = roll_no
        self.class_name = class_name


# class Faculty(User):
#     """Faculty member model."""

#     def __init__(self, employee_id, name):
#         super().__init__(name)
#         self.employee_id = employee_id


class Subject:
    """Represents an academic subject."""

    def __init__(self, code, name):
        self.code = code
        self.name = name


class Attendance:
    """Represents one student's attendance for one subject and date."""

    def __init__(self, student_id, subject_id, attendance_date, status):
        if status not in ("Present", "Absent"):
            raise ValueError("Status must be Present or Absent.")

        self.student_id = student_id
        self.subject_id = subject_id
        self.attendance_date = attendance_date
        self.status = status

    def is_present(self):
        return self.status == "Present"
