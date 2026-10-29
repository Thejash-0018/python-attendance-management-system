"""Report generation, filtering and CSV export (CO2 and CO4)."""
from database import get_attendance_records, get_attendance_summary


def get_summaries():
    """Return report rows; pandas is used if it is installed."""
    rows = [dict(row) for row in get_attendance_summary()]

    try:
        import pandas as pd

        frame = pd.DataFrame(rows)
        if not frame.empty:
            frame["percentage"] = frame["percentage"].fillna(0)
            return frame.to_dict(orient="records")
    except ImportError:
        pass

    # Built-in Python fallback means pandas is optional.
    for row in rows:
        row["percentage"] = row["percentage"] or 0

    return rows


def get_low_attendance(threshold=75):
    """Find student/subject pairs with recorded attendance below threshold."""
    return [
        row for row in get_summaries()
        if row["total_classes"] > 0
        and row["percentage"] < threshold
    ]

