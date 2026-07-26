"""Unit tests for garminconnect.parse_activity_detail_metrics.

Pure-function tests over synthetic payloads shaped like the real
``get_activity_details()`` response — no network access or fixtures needed.
"""

import garminconnect


def test_parse_resolves_metrics_by_name():
    details = {
        "metricDescriptors": [
            {"key": "sumDistance", "metricsIndex": 1},
            {"key": "directHeartRate", "metricsIndex": 4},
        ],
        "activityDetailMetrics": [
            {"metrics": [1720000000000, 12.3, 0, 0, 145]},
            {"metrics": [1720000001000, 12.5, 0, 0, 148]},
        ],
    }

    samples = garminconnect.parse_activity_detail_metrics(details)

    assert samples == [
        {"sumDistance": 12.3, "directHeartRate": 145},
        {"sumDistance": 12.5, "directHeartRate": 148},
    ]


def test_parse_skips_descriptor_with_missing_index():
    details = {
        "metricDescriptors": [
            {"key": "sumDistance"},
            {"key": "directHeartRate", "metricsIndex": 1},
        ],
        "activityDetailMetrics": [{"metrics": [0, 145]}],
    }

    samples = garminconnect.parse_activity_detail_metrics(details)

    assert samples == [{"directHeartRate": 145}]


def test_parse_skips_descriptor_with_non_int_index():
    details = {
        "metricDescriptors": [
            {"key": "sumDistance", "metricsIndex": "1"},
            {"key": "directHeartRate", "metricsIndex": 1},
        ],
        "activityDetailMetrics": [{"metrics": [0, 145]}],
    }

    samples = garminconnect.parse_activity_detail_metrics(details)

    assert samples == [{"directHeartRate": 145}]


def test_parse_skips_descriptor_with_negative_index():
    details = {
        "metricDescriptors": [
            {"key": "sumDistance", "metricsIndex": -1},
            {"key": "directHeartRate", "metricsIndex": 1},
        ],
        "activityDetailMetrics": [{"metrics": [0, 145]}],
    }

    samples = garminconnect.parse_activity_detail_metrics(details)

    assert samples == [{"directHeartRate": 145}]


def test_parse_omits_key_when_sample_shorter_than_index():
    details = {
        "metricDescriptors": [
            {"key": "sumDistance", "metricsIndex": 0},
            {"key": "directHeartRate", "metricsIndex": 4},
        ],
        "activityDetailMetrics": [
            {"metrics": [12.3]},  # missing the heart-rate channel entirely
            {"metrics": [12.5, 0, 0, 0, 148]},
        ],
    }

    samples = garminconnect.parse_activity_detail_metrics(details)

    assert samples == [
        {"sumDistance": 12.3},
        {"sumDistance": 12.5, "directHeartRate": 148},
    ]


def test_parse_keeps_distinct_duration_keys_unchanged():
    details = {
        "metricDescriptors": [
            {"key": "sumDuration", "metricsIndex": 0},
            {"key": "sumElapsedDuration", "metricsIndex": 1},
            {"key": "sumMovingDuration", "metricsIndex": 2},
        ],
        "activityDetailMetrics": [{"metrics": [100, 120, 90]}],
    }

    samples = garminconnect.parse_activity_detail_metrics(details)

    assert samples == [
        {"sumDuration": 100, "sumElapsedDuration": 120, "sumMovingDuration": 90}
    ]


def test_parse_handles_missing_top_level_keys():
    assert garminconnect.parse_activity_detail_metrics({}) == []


def test_parse_handles_null_top_level_values():
    details = {"metricDescriptors": None, "activityDetailMetrics": None}
    assert garminconnect.parse_activity_detail_metrics(details) == []
