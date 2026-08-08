import argparse
from datetime import datetime, timezone


def validate_date(date_string):
    try:
        date = datetime.strptime(date_string, "%Y-%m-%d")  # returns sth like datetime.datetime(2026, 7, 13, 0, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: '{date_string}'. Must be in YYYY-MM-DD format."
        ) from exc  # 'from exc' tells Python: "This new error happened because of the original ValueError"

    # Check future date
    today = datetime.today().date()
    if date.date() > today:
        raise argparse.ArgumentTypeError("Future dates are not allowed.")
    
    return date


def format_date_only(val):
    """Format a date/datetime string or object to YYYY-MM-DD."""
    if not val:
        return None
    val_str = str(val).strip()
    # Handle ISO datetime strings (e.g., '2026-08-05 00:00:00' or '2026-08-05T00:00:00')
    if " " in val_str:
        return val_str.split(" ")[0]
    if "T" in val_str:
        return val_str.split("T")[0]
    return val_str


def format_datetime_utc(iso_str):
    """Convert an ISO datetime string into 'YYYY-MM-DD HH:MM UTC' format."""
    if not iso_str or iso_str == "N/A":
        return "N/A"
    try:
        # Parse the ISO timestamp string into a datetime object
        dt = datetime.fromisoformat(iso_str)
        # Ensure it is converted to UTC timezone
        dt_utc = dt.astimezone(timezone.utc)
        return dt_utc.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, TypeError):
        # Fallback if string format is unexpected
        return str(iso_str)[:16].replace("T", " ") + " UTC"