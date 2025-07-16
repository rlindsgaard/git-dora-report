from datetime import datetime, timedelta
import json
from unittest.mock import MagicMock, patch

import pytest

from dora_report.main import main, parse_interval, chunk_interval

def test_main(script_runner):
    result = script_runner.run("dora_report/main.py --since 2025-07-12 --until 2025-07-14 --interval 1d -vv example_plugin", check=True, shell=True)

    lines = result.stdout.splitlines()
    assert len(lines)
    
    for line in lines:
        result = json.loads(line)
        assert "start" in result
        assert "end" in result
        assert "duration" in result
        assert "deployment_frequency" in result
        assert "change_failure_rate" in result
        assert "mean_time_to_recover" in result
        assert "lead_time_for_changes" in result 


@pytest.fixture
def interval_chunks():
    with patch("dora_report.main.chunk_interval") as p:
        p.return_value = iter(
            [
                {
                    "start": datetime(2025, 7, 12),
                    "end": datetime(2025, 7, 13),
                    "duration": timedelta(days=1),
                    "last_failure": None,
                    "events": [
                        FakeEvent(stamp=datetime(2025, 7, 12, 9, 0, 0), success=True),
                        FakeEvent(stamp=datetime(2025, 7, 12, 11, 55, 0), success=True),
                        FakeEvent(stamp=datetime(2025, 7, 12, 15, 15, 0), success=True),
                    ],
                },
                {
                    "start": datetime(2025, 7, 13),
                    "end": datetime(2025, 7, 14),
                    "duration": timedelta(days=1),
                    "last_failure": None,
                    "events": [
                        FakeEvent(stamp=datetime(2025, 7, 13, 8, 5, 0), success=True),
                        FakeEvent(stamp=datetime(2025, 7, 13, 10, 0), success=True),
                    ],
                },
            ]
        )
        yield p

def test_dora_report_records(interval_chunks, root_logger):
    args = Namespace()
    args.collector = MagicMock()
    args.since = datetime(2025, 7, 12)
    args.until = datetime(2025, 7, 14)
    args.log = root_logger
    
    report = DoraReport(args)
    report.analyze()
    assert report.records == []


@pytest.mark.parametrize(
    "interval_str, expected_output",
    [
        ("7d", 7.0),    # Valid days
        ("2w", 14.0),   # Valid weeks
        ("1m", 30.0),   # Valid months
    ]
)
def test_parse_interval_valid(interval_str, expected_output):
    assert parse_interval(interval_str) / 86400 == expected_output

@pytest.mark.parametrize(
    "interval_str, expected_exception_message",
    [
        ("10", "Invalid interval format. Use Nd, Nw, or Nm (e.g., 7d, 2w, 1m)"),  # Missing suffix
        ("5y", "Invalid interval format. Use Nd, Nw, or Nm (e.g., 7d, 2w, 1m)"),  # Unknown suffix
        ("", "Invalid interval format. Use Nd, Nw, or Nm (e.g., 7d, 2w, 1m)"),    # Empty string
    ]
)
def test_parse_interval_invalid(interval_str, expected_exception_message):
    with pytest.raises(ValueError) as exc_info:
        parse_interval(interval_str)
    assert str(exc_info.value) == expected_exception_message

def test_chunk_interval():
    class FakeEvent:
        def __init__(self, stamp, success=None):
            self.stamp = stamp
            self.success = success
            
        def __eq__(self, other): 
            if self.stamp == other.stamp:
                return self.success == other.success
            return False

        def __str__(self):
            return f"FakeEvent<{stamp=}, {success=}>"  
 
    events = [
        FakeEvent(stamp=datetime(2025, 7, 12, 9, 0, 0), success=True),
        FakeEvent(stamp=datetime(2025, 7, 12, 11, 55, 0), success=True),
        FakeEvent(stamp=datetime(2025, 7, 12, 15, 15, 0), success=True),
        FakeEvent(stamp=datetime(2025, 7, 13, 8, 5, 0), success=True),
        FakeEvent(stamp=datetime(2025, 7, 13, 10, 0), success=True),
        FakeEvent(stamp=datetime(2025, 7, 14, 9, 5, 0), success=True),
    ]
    
    actual = list(chunk_interval(
        iter(events), 
        since=datetime(2025, 7, 12, 0, 0, 0),
        size=86400,
        until=datetime(2025, 7, 14, 0, 0, 0),
    ))
    
    expect = [
        {
            "start": datetime(2025, 7, 12),
            "end": datetime(2025, 7, 13),
            "duration": timedelta(days=1),
            "last_failure": None,
            "events": [
                FakeEvent(stamp=datetime(2025, 7, 12, 9, 0, 0), success=True),
                FakeEvent(stamp=datetime(2025, 7, 12, 11, 55, 0), success=True),
                FakeEvent(stamp=datetime(2025, 7, 12, 15, 15, 0), success=True),
            ],
        },
        {
            "start": datetime(2025, 7, 13),
            "end": datetime(2025, 7, 14),
            "duration": timedelta(days=1),
            "last_failure": None,
            "events": [
                FakeEvent(stamp=datetime(2025, 7, 13, 8, 5, 0), success=True),
                FakeEvent(stamp=datetime(2025, 7, 13, 10, 0), success=True),
            ],
        },
    ]
    
    assert expect == actual 
        