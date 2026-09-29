"""FIT timestamps represent UTC instants, independent of the host timezone."""

import time
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from garminconnect.fit import FitEncoder  # type: ignore[attr-defined]


@pytest.fixture(params=["UTC0", "EST5EDT,M3.2.0,M11.1.0"])
def local_timezone(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Iterator[None]:
    if not hasattr(time, "tzset"):
        pytest.skip("changing the process timezone requires time.tzset")
    try:
        with monkeypatch.context() as env:
            env.setenv("TZ", request.param)
            time.tzset()
            yield
    finally:
        time.tzset()


@pytest.mark.usefixtures("local_timezone")
@pytest.mark.parametrize(
    "value",
    [
        "2026-07-01T03:00:00+00:00",
        "2026-07-01T08:45:00+05:45",
        "2026-06-30T20:00:00-07:00",
    ],
)
def test_aware_datetimes_encode_the_same_instant(value: str):
    expected = (
        datetime(2026, 7, 1, 3, tzinfo=UTC) - datetime(1989, 12, 31, tzinfo=UTC)
    ).total_seconds()
    assert FitEncoder().timestamp(datetime.fromisoformat(value)) == expected


@pytest.mark.usefixtures("local_timezone")
@pytest.mark.parametrize("month", [1, 7])
def test_naive_datetimes_remain_local_time(month: int):
    value = datetime(2026, month, 1, 12, 30)
    expected = time.mktime(value.timetuple()) - 631065600
    assert FitEncoder().timestamp(value) == expected


@pytest.mark.parametrize("value", [631065600, 631065601.5])
def test_numeric_unix_timestamps(value: float):
    assert FitEncoder().timestamp(value) == value - 631065600
