"""Golf scorecards, shots and club statistics."""

import re
from typing import Any

from ._common import (
    _coerce_positive_id,
    _validate_hole_numbers,
    _validate_non_negative_integer,
    _validate_positive_integer,
    logger,
)
from .base import GarminBase


class GolfMixin(GarminBase):
    """Golf scorecards, shots and club statistics."""

    def get_golf_summary(
        self, start: int = 0, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Return golf scorecard summary.

        Args:
            start: Starting offset for pagination.
            limit: Maximum number of results to return.

        Returns:
            List of golf scorecard summaries.

        """
        start = _validate_non_negative_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        url = f"{self.garmin_golf_scorecard_summary}"
        params = {"per-page": str(limit), "start": str(start)}
        logger.debug("Requesting golf summary with limit %d", limit)
        return self.connectapi(url, params=params)

    def get_golf_scorecard(self, scorecard_id: int | str) -> dict[str, Any]:
        """Return golf scorecard detail by scorecard ID.

        Args:
            scorecard_id: The scorecard ID to retrieve.

        Returns:
            Dictionary containing the golf scorecard detail.

        """
        scorecard_id = _coerce_positive_id(scorecard_id, "scorecard_id")
        url = f"{self.garmin_golf_scorecard_detail}"
        params = {
            "scorecard-ids": str(scorecard_id),
            "include-longest-shot-distance": "true",
        }
        logger.debug("Requesting golf scorecard %d", scorecard_id)
        return self.connectapi(url, params=params)

    def get_golf_shot_data(
        self,
        scorecard_id: int | str,
        hole_numbers: str | None = None,
    ) -> dict[str, Any]:
        """Return golf shot data for a scorecard and specific holes.

        Args:
            scorecard_id: The scorecard ID to get shot data for.
            hole_numbers: Holes 1-18 separated by ',' or '-' (e.g. "1,2,3").
                Garmin's API only accepts '-' as a separator, so any commas
                are normalized to '-' before the request is sent.
                Lists containing holes 10-18 are silently upgraded to return
                all 18 holes, because Garmin's endpoint drops double-digit
                hole numbers from filtered queries.
                Omit to get every hole on the scorecard.

        Returns:
            Dictionary containing shot data per hole.

        """
        scorecard_id = _coerce_positive_id(scorecard_id, "scorecard_id")
        url = f"{self.garmin_golf_shot}/{scorecard_id}/hole"
        params = None
        if hole_numbers is not None:
            hole_numbers = _validate_hole_numbers(hole_numbers)
            # Garmin's endpoint only returns single-digit holes reliably when a
            # hole-numbers filter is supplied. Double-digit holes (10-18) are
            # dropped or cause an empty response. The only reliable way to
            # retrieve holes 10-18 is to omit the parameter and get all 18 holes.
            if any(int(n) > 9 for n in re.findall(r"\d+", hole_numbers)):
                logger.warning(
                    "Garmin drops double-digit hole numbers from hole-numbers "
                    "queries; returning all 18 holes for scorecard %s instead of %s",
                    scorecard_id,
                    hole_numbers,
                )
                hole_numbers = None
            else:
                params = f"hole-numbers={hole_numbers.replace(',', '-')}"
        logger.debug(
            "Requesting golf shot data for scorecard %d, holes %s",
            scorecard_id,
            "all" if hole_numbers is None else hole_numbers,
        )
        return self.connectapi(url, params=params)

    def get_golf_club_stats(
        self,
        limit: int = 1000,
    ) -> dict[str, Any]:
        """Return golf club names and statistics.

        Args:
            limit: Maximum number of results to return.

        Returns:
            Dictionary containing club list and distance data.

        """
        limit = _validate_positive_integer(limit, "limit")
        url = f"{self.garmin_golf_club_stats}"
        params = {"per-page": str(limit), "include-stats": "true"}
        logger.debug("Requesting golf club data for the user.")
        return self.connectapi(url, params=params)

    def get_golf_user_stats(self) -> dict[str, Any]:
        """Return an overview of the user's golf statistics.

        Returns:
            Dictionary containing user stats such as handicap and strokes gained.

        """
        url = f"{self.garmin_golf_user_stats}"
        logger.debug("Requesting golf user statistics")
        return self.connectapi(url)
