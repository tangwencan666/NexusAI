import re
import uuid
from datetime import date, datetime
from enum import Enum
from decimal import Decimal
from typing import Any

SENSITIVE_KEYS = {"authorization", "api_key", "apikey", "password", "secret", "token", "cookie"}


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~-]+", r"\1[REDACTED]", value)
    if isinstance(value, (uuid.UUID, date, datetime, Enum)):
        return str(getattr(value, "value", value))
    if isinstance(value, Decimal):
        return float(value)
    return value
