"""Python 3 API wrapper for Garmin Connect."""

import time  # noqa: F401  (re-exported: callers patch garminconnect.time.sleep)

from . import client as client
from .activity_details import (
    parse_activity_detail_metrics as parse_activity_detail_metrics,
)
from .api import Garmin as Garmin
from .api._common import (  # noqa: F401
    _STATUS_CODE_RE,
    DATE_FORMAT_REGEX,
    DATE_FORMAT_STR,
    HOLE_NUMBERS_REGEX,
    JETLAG_FLIGHT_KEYS,
    MAX_ACTIVITY_LIMIT,
    MAX_HYDRATION_ML,
    MAX_PAGINATED_REQUESTS,
    SPORT_KEY_REGEX,
    UTC_OFFSET_MAX_MINUTES,
    UTC_OFFSET_MIN_MINUTES,
    UTC_OFFSET_REGEX,
    VALID_DAILY_STATS_TYPES,
    VALID_MENSTRUAL_DISCHARGE,
    VALID_MENSTRUAL_FLOW,
    VALID_MENSTRUAL_MOODS,
    VALID_MENSTRUAL_REPORT_CYCLES,
    VALID_MENSTRUAL_SEX_DRIVE,
    VALID_MENSTRUAL_SEXUAL_ACTIVITY,
    VALID_MENSTRUAL_SYMPTOMS,
    VALID_WEIGHT_UNITS,
    VALID_WORKOUT_ORDER_BY,
    _backoff_delay,
    _clean_menstrual_daily_log,
    _coerce_positive_id,
    _extract_status_code,
    _fmt_ts,
    _fmt_ts_utc,
    _handle_api_errors,
    _has_network_cause,
    _is_legacy_garth_tokenstore,
    _is_retryable,
    _looks_like_json,
    _validate_date_format,
    _validate_date_group_list,
    _validate_date_range,
    _validate_hole_numbers,
    _validate_jetlag_flights,
    _validate_json_exists,
    _validate_menstrual_enum,
    _validate_menstrual_enum_list,
    _validate_non_negative_integer,
    _validate_positive_integer,
    _validate_positive_number,
    _validate_sport_key,
    _validate_uuid,
    logger,
)
from .exceptions import (
    GarminConnectAuthenticationError as GarminConnectAuthenticationError,
)
from .exceptions import (
    GarminConnectConnectionError as GarminConnectConnectionError,
)
from .exceptions import (
    GarminConnectInvalidFileFormatError as GarminConnectInvalidFileFormatError,
)
from .exceptions import (
    GarminConnectNotFoundError as GarminConnectNotFoundError,
)
from .exceptions import (
    GarminConnectTooManyRequestsError as GarminConnectTooManyRequestsError,
)
