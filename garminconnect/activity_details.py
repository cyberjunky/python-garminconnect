"""Helpers for parsing the positional metrics returned by activity detail endpoints."""

from __future__ import annotations

from typing import Any


def parse_activity_detail_metrics(details: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve positional activity detail samples into per-sample dicts keyed by metric name.

    `details` is the raw response from `Garmin.get_activity_details()`. Each sample in
    `activityDetailMetrics` stores values positionally in `metrics`; the position-to-name
    mapping is given by `metricDescriptors[].metricsIndex`/`key` and varies by device and
    activity type. Descriptors with a missing, non-int, or negative `metricsIndex` are
    skipped, and a sample missing a channel entirely (index out of range for that sample)
    simply omits that key rather than raising. Duration keys (`sumDuration`,
    `sumElapsedDuration`, `sumMovingDuration`) are not equivalent and are passed through
    unchanged under their own names — callers must pick the one they mean.
    """
    index_to_key: dict[int, str] = {}
    for descriptor in details.get("metricDescriptors") or []:
        key = descriptor.get("key")
        index = descriptor.get("metricsIndex")
        if (
            not isinstance(key, str)
            or not isinstance(index, int)
            or isinstance(index, bool)
        ):
            continue
        if index < 0:
            continue
        index_to_key[index] = key

    parsed: list[dict[str, Any]] = []
    for sample in details.get("activityDetailMetrics") or []:
        metrics = sample.get("metrics") or []
        parsed.append(
            {
                key: metrics[index]
                for index, key in index_to_key.items()
                if index < len(metrics)
            }
        )
    return parsed
