import pytest

import garminconnect


DATE = "2023-07-01"


@pytest.fixture(scope="session")
def garmin():
    return garminconnect.Garmin("email", "password")


@pytest.mark.vcr
def test_stats(garmin):
    garmin.login()
    stats = garmin.get_stats(DATE)
    assert "totalKilocalories" in stats
    assert "activeKilocalories" in stats
