import re
from app import app, api, mongo
from datetime import datetime, date, timedelta, timezone as pythontz

#DATABASE collections
students = mongo.db.students



def is_valid_gmail(email: str) -> bool:
    """
    Validate a Gmail address strictly.
    Returns True if valid Gmail, False otherwise.
    """

    if not isinstance(email, str) or not email:
        return False

    # Regex for Gmail
    gmail_regex = re.compile(
        r"^(?!\.)"                 # cannot start with dot
        r"(?!.*\.\.)"              # no consecutive dots
        r"[a-zA-Z0-9](?:[a-zA-Z0-9._]{4,28}[a-zA-Z0-9])?"  # local part
        r"@gmail\.com$"            # must end with @gmail.com
    )

    return re.match(gmail_regex, email) is not None


def is_valid_nigerian_number(phone: str) -> bool:
    """
    Validate Nigerian phone numbers.
    Accepts local (11 digits) and international (+234 / 234) formats.
    """

    if not isinstance(phone, str) or not phone:
        return False

    # Remove spaces and dashes
    phone = phone.strip().replace(" ", "").replace("-", "")

    # Regex patterns
    local_pattern = re.compile(r"^(0)(70|80|81|90|91)\d{8}$")      # 11 digits
    intl_pattern = re.compile(r"^(\+234|234)(70|80|81|90|91)\d{8}$")  # 13 digits

    return bool(local_pattern.match(phone) or intl_pattern.match(phone))


def normalize_name(value: str) -> str:
    """Capitalize first letter, rest lower."""
    return value.strip().capitalize()


def normalize_email(value: str) -> str:
    """Always store email in lowercase."""
    return value.strip().lower()


def normalize_phone(value: str) -> str:
    """Remove spaces and keep as string."""
    return value.strip()


def normalize_word(value: str) -> str:
    """Capitalize first letter only (for Gender, Role, Admission type)."""
    return value.strip().capitalize()
