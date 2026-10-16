"""Constants, validation helpers and the retry decorator shared by the API mixins."""

import functools
import logging
import math
import numbers
import random
import re
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import requests
from requests import HTTPError

from ..exceptions import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectNotFoundError,
    GarminConnectTooManyRequestsError,
)

logger = logging.getLogger(__name__)

# Regex used to extract an HTTP status code from the client's error messages.
# The underlying client raises GarminConnectConnectionError with a message of
# the form "API Error {status} - {detail}", so we parse it to decide whether
# a failure is retryable (5xx) or not (4xx, auth, etc.).
_STATUS_CODE_RE = re.compile(r"(?:API Error|Error|HTTP)\s*(\d{3})")

# Constants for validation
MAX_ACTIVITY_LIMIT = 1000
MAX_HYDRATION_ML = 10000  # 10 liters
# Safety cap on server-driven pagination loops (get_activities_by_date,
# get_goals). Termination of those loops otherwise depends entirely on the
# server eventually returning an empty page, so a hostile/broken server could
# loop the client forever with unbounded memory growth. 2000 pages at 20-30
# items per page (40k-60k items) is far beyond any legitimate account.
MAX_PAGINATED_REQUESTS = 2000
DATE_FORMAT_REGEX = r"^\d{4}-\d{2}-\d{2}$"
DATE_FORMAT_STR = "%Y-%m-%d"

# Holes 1-18, separated by ',' or '-'; '-' is a plain delimiter, not a range
# operator (e.g. "1-18" selects holes 1 and 18, not the full front/back).
# Garmin's API only accepts '-' as the separator (commas 400 in any encoding),
# so callers may pass ',' for convenience but it gets normalized to '-' before
# the request is sent.
HOLE_NUMBERS_REGEX = r"^([1-9]|1[0-8])([,-]([1-9]|1[0-8]))*$"
SPORT_KEY_REGEX = r"^[A-Z_]+$"
VALID_WEIGHT_UNITS = {"kg", "lbs"}
# Sort keys accepted by the workout library (workout-service/workouts?orderBy=)
VALID_WORKOUT_ORDER_BY = frozenset(
    {
        "WORKOUT_NAME",
        "WORKOUT_SPORT_PK",
        "CREATED_DATE",
        "UPDATE_DATE",
        "WORKOUT_PROVIDER",
    }
)
# Series accepted by usersummary-service/stats/daily?statsType=
VALID_DAILY_STATS_TYPES = frozenset({"STEPS", "PUSHES", "CALORIES"})
VALID_MENSTRUAL_FLOW = frozenset({"LIGHT", "MEDIUM", "HEAVY"})
VALID_MENSTRUAL_SYMPTOMS = frozenset(
    {
        "ACNE",
        "BACKACHE",
        "BLOATING",
        "BODY_ACHES",
        "CONSTIPATION",
        "CRAMPS",
        "CRAVINGS",
        "DIARRHEA",
        "DIZZINESS",
        "FATIGUE",
        "HEADACHE",
        "INSOMNIA",
        "NAUSEA",
        "TENDER_BREASTS",
    }
)
VALID_MENSTRUAL_MOODS = frozenset(
    {
        "ENERGETIC",
        "EMOTIONAL",
        "FINE",
        "FRUSTRATED",
        "HAPPY",
        "IRRITABLE",
        "MOOD_SWINGS",
        "MOTIVATED",
        "OVERWHELMED",
        "SAD",
    }
)
VALID_MENSTRUAL_DISCHARGE = frozenset(
    {
        "CREAMY",
        "EGG_WHITE",
        "NO_DISCHARGE",
        "SPOTTING",
        "STICKY",
        "UNUSUAL",
    }
)
VALID_MENSTRUAL_SEX_DRIVE = frozenset({"AVERAGE", "HIGH", "LOW"})
VALID_MENSTRUAL_SEXUAL_ACTIVITY = frozenset({"PROTECTED", "UNPROTECTED"})
VALID_MENSTRUAL_REPORT_CYCLES = frozenset({1, 6, 12})
JETLAG_FLIGHT_KEYS = (
    "originLocation",
    "originTimezone",
    "originTimestamp",
    "destinationLocation",
    "destinationTimezone",
    "destinationTimestamp",
)
UTC_OFFSET_REGEX = r"^([+-])(\d{2}):([0-5]\d)$"
# Real UTC offsets run from -12:00 to +14:00.
UTC_OFFSET_MIN_MINUTES = -12 * 60
UTC_OFFSET_MAX_MINUTES = 14 * 60


# Add validation utilities
def _validate_date_format(date_str: str, param_name: str = "date") -> str:
    """Validate date string format YYYY-MM-DD."""
    if not isinstance(date_str, str):
        raise ValueError(f"{param_name} must be a string")

    # Remove any extra whitespace
    date_str = date_str.strip()

    if not re.fullmatch(DATE_FORMAT_REGEX, date_str):
        raise ValueError(
            f"{param_name} must be in format 'YYYY-MM-DD', got: {date_str}"
        )

    try:
        # Validate that it's a real date
        datetime.strptime(date_str, DATE_FORMAT_STR)
    except ValueError as e:
        raise ValueError(f"invalid {param_name}: {e}") from e

    return date_str


def _validate_date_range(start: str, end: str) -> tuple[str, str]:
    """Validate 'start'/'end' are well-formed dates with start <= end."""
    start = _validate_date_format(start, "start")
    end = _validate_date_format(end, "end")
    if datetime.strptime(start, DATE_FORMAT_STR) > datetime.strptime(
        end, DATE_FORMAT_STR
    ):
        raise ValueError("start date cannot be after end date")
    return start, end


def _validate_positive_number(
    value: int | float, param_name: str = "value"
) -> int | float:
    """Validate that a number is positive and finite."""
    if not isinstance(value, numbers.Real):
        raise ValueError(f"{param_name} must be a number")

    if isinstance(value, bool):
        raise ValueError(f"{param_name} must be a number, not bool")

    if not math.isfinite(value):
        raise ValueError(f"{param_name} must be finite, got: {value}")

    if value <= 0:
        raise ValueError(f"{param_name} must be positive, got: {value}")

    return value


def _validate_non_negative_integer(value: int, param_name: str = "value") -> int:
    """Validate that a value is a non-negative integer."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{param_name} must be an integer")

    if value < 0:
        raise ValueError(f"{param_name} must be non-negative, got: {value}")

    return value


def _validate_positive_integer(value: int, param_name: str = "value") -> int:
    """Validate that a value is a positive integer."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{param_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{param_name} must be a positive integer, got: {value}")
    return value


def _coerce_positive_id(value: Any, param_name: str = "value") -> int:
    """Convert an ID-like value to a positive int without truncating it.

    Accepts ints, whole-number floats (``123.0``) and integer strings
    (``"123"``). Plain ``int()`` would silently turn ``1.9`` into ``1``
    and so target a different resource; that is rejected instead.
    """
    if isinstance(value, bool):
        raise ValueError(f"{param_name} must be an integer")
    if isinstance(value, numbers.Integral):
        result = int(value)
    elif isinstance(value, float):
        if not value.is_integer():
            raise ValueError(f"{param_name} must be a whole number, got: {value}")
        result = int(value)
    elif isinstance(value, str):
        try:
            result = int(value.strip())
        except ValueError:
            raise ValueError(
                f"{param_name} must be an integer, got: {value!r}"
            ) from None
    else:
        raise ValueError(f"{param_name} must be an integer, got: {value!r}")
    return _validate_positive_integer(result, param_name)


def _validate_hole_numbers(value: str, param_name: str = "hole_numbers") -> str:
    """Validate a golf hole-numbers string: holes 1-18 separated by ',' or '-'.

    Spaces around separators are tolerated (e.g. "1, 2, 3" or "1 - 18").
    """
    if not isinstance(value, str):
        raise ValueError(f"{param_name} must be a string")
    # Remove spaces so callers can use "1, 2, 3" or "1 - 18" and still pass
    # a clean hyphen-separated string to Garmin's API.
    value = value.replace(" ", "")
    if not re.fullmatch(HOLE_NUMBERS_REGEX, value):
        raise ValueError(
            f"{param_name} must be holes 1-18 separated by ',' or '-', got: {value!r}"
        )
    return value


def _validate_sport_key(value: str, param_name: str = "sport") -> str:
    """Validate and normalize a Garmin sport key (letters and underscores only)."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{param_name} must be a non-empty string")
    normalized = value.strip().upper()
    if not re.fullmatch(SPORT_KEY_REGEX, normalized):
        raise ValueError(f"{param_name} must contain only letters and underscores")
    return normalized


def _validate_uuid(value: str, param_name: str = "uuid") -> str:
    """Validate a UUID string (with or without hyphens)."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{param_name} must be a non-empty string")
    value = value.strip()
    if not re.fullmatch(
        r"^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$",
        value,
    ):
        raise ValueError(f"{param_name} must be a valid UUID, got: {value!r}")
    return value


def _fmt_ts(dt: datetime) -> str:
    # Use ms precision to match server expectations
    return dt.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]


def _fmt_ts_utc(dt: datetime | None = None) -> str:
    """Format a timestamp the way Garmin Connect menstrual writes expect UTC."""
    if dt is None:
        dt = datetime.now(UTC)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return _fmt_ts(dt)


def _validate_menstrual_enum(
    value: str, valid_values: frozenset[str], param_name: str
) -> str:
    """Validate and normalize a Garmin menstrual enum string."""
    if not isinstance(value, str):
        raise ValueError(f"{param_name} must be a string")
    normalized = value.strip().upper()
    if normalized not in valid_values:
        raise ValueError(
            f"{param_name} must be one of {sorted(valid_values)}, got: {value}"
        )
    return normalized


def _validate_menstrual_enum_list(
    values: list[str] | None, valid_values: frozenset[str], param_name: str
) -> list[str] | None:
    """Validate an optional list of Garmin menstrual enum strings."""
    if values is None:
        return None
    if not isinstance(values, list):
        raise ValueError(f"{param_name} must be a list")
    validated = [
        _validate_menstrual_enum(value, valid_values, f"{param_name}[{index}]")
        for index, value in enumerate(values)
    ]
    unique: list[str] = []
    seen: set[str] = set()
    for value in validated:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


def _validate_date_group_list(
    values: list[list[str]], param_name: str
) -> list[list[str]]:
    """Validate a list of non-empty consecutive YYYY-MM-DD groups."""
    if not isinstance(values, list):
        raise ValueError(f"{param_name} must be a list")
    if not values:
        raise ValueError(f"{param_name} must not be empty")
    result: list[list[str]] = []
    for index, group in enumerate(values):
        if not isinstance(group, list):
            raise ValueError(f"{param_name}[{index}] must be a list")
        if not group:
            raise ValueError(f"{param_name}[{index}] must not be empty")
        days = [
            _validate_date_format(day, f"{param_name}[{index}][{day_index}]")
            for day_index, day in enumerate(group)
        ]
        parsed = [datetime.strptime(day, DATE_FORMAT_STR).date() for day in days]
        for offset in range(1, len(parsed)):
            if parsed[offset] != parsed[offset - 1] + timedelta(days=1):
                raise ValueError(
                    f"{param_name}[{index}] must be consecutive calendar dates"
                )
        result.append(days)
    return result


def _clean_menstrual_daily_log(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop null/empty daily-log fields the way Garmin Connect's helper does."""
    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if hasattr(value, "__len__") and len(value) == 0 and key != "notes":
            continue
        cleaned[key] = value
    return cleaned


def _validate_jetlag_flights(flights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate Jet Lag Adviser flights and return shallow copies."""
    if not isinstance(flights, list) or not flights:
        raise ValueError("flights must be a non-empty list")
    result: list[dict[str, Any]] = []
    for index, flight in enumerate(flights):
        name = f"flights[{index}]"
        if not isinstance(flight, dict):
            raise ValueError(f"{name} must be a dictionary")
        missing = [key for key in JETLAG_FLIGHT_KEYS if not flight.get(key)]
        if missing:
            raise ValueError(f"{name} is missing {', '.join(missing)}")
        for side in ("origin", "destination"):
            offset = flight[f"{side}Timezone"]
            match = (
                re.fullmatch(UTC_OFFSET_REGEX, offset)
                if isinstance(offset, str)
                else None
            )
            minutes = None
            if match:
                sign = -1 if match.group(1) == "-" else 1
                minutes = sign * (int(match.group(2)) * 60 + int(match.group(3)))
            if minutes is None or not (
                UTC_OFFSET_MIN_MINUTES <= minutes <= UTC_OFFSET_MAX_MINUTES
            ):
                raise ValueError(
                    f"{name}.{side}Timezone must be a UTC offset between "
                    f"'-12:00' and '+14:00', such as '-07:00', got: {offset!r}"
                )
            raw_stamp = flight[f"{side}Timestamp"]
            # fromisoformat() reads a date alone as midnight.
            if not isinstance(raw_stamp, str) or "T" not in raw_stamp:
                raise ValueError(
                    f"invalid {name}.{side}Timestamp: must hold a date and a "
                    f"time such as '2026-10-04T15:20:00', got: {raw_stamp!r}"
                )
            try:
                stamp = datetime.fromisoformat(raw_stamp)
            except ValueError as e:
                raise ValueError(f"invalid {name}.{side}Timestamp: {e}") from e
            if stamp.tzinfo is not None:
                raise ValueError(
                    f"{name}.{side}Timestamp must be local time without an offset"
                )
        result.append(dict(flight))
    return result


def _validate_json_exists(response: requests.Response) -> dict[str, Any] | None:
    if response.status_code == 204:
        return None
    return response.json()


def _looks_like_json(value: str) -> bool:
    """Return True if the value appears to be JSON rather than a file path.

    The tokenstore argument may be either a filesystem path or an inline JSON
    token string. Structural detection is more reliable than a length threshold,
    which misclassifies long legitimate paths as JSON and short JSON strings as
    paths.
    """
    stripped = value.strip()
    return stripped.startswith(("{", "["))


def _is_legacy_garth_tokenstore(path: str) -> bool:
    """Return True if path is a directory holding only old garth-format tokens.

    Versions before 0.3 saved sessions with garth (oauth1_token.json and
    oauth2_token.json). Those tokens cannot be converted, so callers use this
    to explain why the tokenstore did not load instead of a generic error.
    """
    token_dir = Path(path).expanduser()
    try:
        return token_dir.is_dir() and (
            not (token_dir / "garmin_tokens.json").exists()
            and (
                (token_dir / "oauth1_token.json").exists()
                or (token_dir / "oauth2_token.json").exists()
            )
        )
    except OSError:
        return False


def _extract_status_code(exc: BaseException) -> int | None:
    """Best-effort extraction of an HTTP status code from an exception.

    Checks ``status_code`` and ``response.status_code`` attributes, then
    parses ``"API Error NNN"`` / ``"HTTP NNN"`` patterns out of the message
    (the client raises ``GarminConnectConnectionError`` with messages like
    ``"API Error 503 - ..."``).
    """
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status
    resp = getattr(exc, "response", None)
    status = getattr(resp, "status_code", None)
    if isinstance(status, int):
        return status
    match = _STATUS_CODE_RE.search(str(exc))
    return int(match.group(1)) if match else None


def _has_network_cause(exc: BaseException) -> bool:
    """Walk ``__cause__`` / ``__context__`` looking for a raw network error."""
    seen: set[int] = set()
    cur: BaseException | None = exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        if isinstance(cur, requests.ConnectionError | requests.Timeout):
            return True
        cur = cur.__cause__ or cur.__context__
    return False


def _is_retryable(exc: BaseException) -> bool:
    """Return True for transient errors worth retrying.

    Retries 5xx server errors and genuine network failures. Never retries
    401 (auth), 429 (rate-limit) or 4xx (client) errors — those are
    deterministic and caller-actionable.
    """
    if isinstance(
        exc, GarminConnectAuthenticationError | GarminConnectTooManyRequestsError
    ):
        return False
    if isinstance(exc, GarminConnectConnectionError):
        status = _extract_status_code(exc)
        if status is None:
            return _has_network_cause(exc)
        return 500 <= status < 600
    return isinstance(exc, requests.ConnectionError | requests.Timeout)


def _backoff_delay(attempt: int, obj: Any) -> float:
    """Exponential backoff with 50-100% jitter, bounded by ``retry_max_wait``."""
    min_wait = getattr(obj, "retry_min_wait", 1.0)
    max_wait = getattr(obj, "retry_max_wait", 10.0)
    base = min(max_wait, min_wait * (2**attempt))
    return base * (0.5 + random.random() * 0.5)  # noqa: S311  jitter, not crypto


def _handle_api_errors(
    label: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator: uniform error translation + optional retry for Garmin API calls.

    Translates transport-level exceptions to domain-specific
    ``GarminConnectAuthenticationError`` (401), ``GarminConnectTooManyRequestsError``
    (429) or ``GarminConnectConnectionError`` (all other HTTP / network failures),
    preserving the original ``.response`` where available so callers can still
    introspect the underlying response.

    Retries are controlled by ``self.retry_attempts`` (default ``3``; set to
    ``0`` to disable). When enabled, only 5xx server errors and raw connection
    / timeout failures are retried, with exponential backoff plus jitter
    between ``retry_min_wait`` and ``retry_max_wait`` seconds. 401 / 429 / 4xx
    always fail fast.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            path = args[0] if args else kwargs.get("path", "<unknown>")
            attempts = max(0, getattr(self, "retry_attempts", 0))
            for attempt in range(attempts + 1):
                try:
                    return func(self, *args, **kwargs)
                except (
                    GarminConnectAuthenticationError,
                    GarminConnectTooManyRequestsError,
                ):
                    # Already domain-specific and never retryable.
                    raise
                except (HTTPError, GarminConnectConnectionError) as e:
                    status = _extract_status_code(e)
                    if status == 401:
                        raise GarminConnectAuthenticationError(
                            f"Authentication failed: {e}"
                        ) from e
                    if status == 429:
                        raise GarminConnectTooManyRequestsError(
                            f"Rate limit exceeded: {e}"
                        ) from e
                    if status == 404:
                        not_found_exc = GarminConnectNotFoundError(
                            f"{label} client error ({status}): {e}"
                        )
                        resp = getattr(e, "response", None)
                        if resp is not None:
                            not_found_exc.response = resp
                        raise not_found_exc from e
                    if status and 400 <= status < 500:
                        new_exc = GarminConnectConnectionError(
                            f"{label} client error ({status}): {e}"
                        )
                        resp = getattr(e, "response", None)
                        if resp is not None:
                            new_exc.response = resp
                        raise new_exc from e
                    # Retry only transient failures: a 5xx, or no status but a
                    # network error in the cause chain. A status-less local
                    # error (rejected URL, invalid response) cannot succeed.
                    retryable = (
                        _has_network_cause(e) if status is None else status >= 500
                    )
                    if retryable and attempt < attempts:
                        delay = _backoff_delay(attempt, self)
                        logger.warning(
                            "%s attempt %d/%d failed (path=%s status=%s) — "
                            "retrying in %.1fs: %s",
                            label,
                            attempt + 1,
                            attempts + 1,
                            path,
                            status,
                            delay,
                            e,
                        )
                        time.sleep(delay)
                        continue
                    logger.exception(
                        "%s failed for path '%s' (status=%s)", label, path, status
                    )
                    new_exc = GarminConnectConnectionError(f"{label} HTTP error: {e}")
                    resp = getattr(e, "response", None)
                    if resp is not None:
                        new_exc.response = resp
                    raise new_exc from e
                except (requests.ConnectionError, requests.Timeout) as e:
                    if attempt < attempts:
                        delay = _backoff_delay(attempt, self)
                        logger.warning(
                            "%s network error attempt %d/%d (path=%s) — "
                            "retrying in %.1fs: %s",
                            label,
                            attempt + 1,
                            attempts + 1,
                            path,
                            delay,
                            e,
                        )
                        time.sleep(delay)
                        continue
                    logger.exception("Network error during %s path=%s", label, path)
                    raise GarminConnectConnectionError(f"Connection error: {e}") from e
                except Exception as e:
                    logger.exception("Connection error during %s path=%s", label, path)
                    raise GarminConnectConnectionError(f"Connection error: {e}") from e
            # Unreachable: loop returns, retries, or raises.
            raise RuntimeError(f"{label} retry loop exited without a result")

        return wrapper

    return decorator
