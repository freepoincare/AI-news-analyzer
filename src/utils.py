import argparse
from datetime import datetime


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