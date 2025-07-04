import pytest
from datetime import datetime, timedelta
from dora_report.models import ChangeEvent
from dora_report.metrics import (
    change_frequency, 
    change_failure_rate,
) 

@pytest.mark.parametrize(
    "change_events, duration, expected",
    [
        # Zero ChangeEvents
        ([], timedelta(days=7), 0.0),
        ([], timedelta(days=1), 0.0),

        # One ChangeEvent
        (
            [
                ChangeEvent(
                    identifier="1", 
                    stamp=datetime(2023, 1, 1, 12, 0, 0), 
                    success=True,
                    lead_time=timedelta(seconds=3600)
                )
            ], 
            timedelta(days=7), 
            0.00000165344
        ),
        (
            [
                ChangeEvent(
                    identifier="1", 
                    stamp=datetime(2023, 1, 1, 12, 0, 0), 
                    success=True, 
                    lead_time=timedelta(seconds=3600)
                )
            ], 
            timedelta(days=1), 
            0.00001157407407
        ),

        # Seven ChangeEvents
        (
            [
                ChangeEvent(
                    identifier=str(i), 
                    stamp=datetime(2023, 1, 1, 12, 0, 0), 
                    success=True, 
                    lead_time=timedelta(seconds=3600)
                ) 
                for i in range(7)
            ], 
            timedelta(days=7), 
            0.00001157407407
        ),
        (
            [
                ChangeEvent(
                    identifier=str(i), 
                    stamp=datetime(2023, 1, 1, 12, 0, 0), 
                    success=True, 
                    lead_time=timedelta(seconds=3600)
                ) 
                for i in range(7)
            ], 
            timedelta(days=1), 
            0.00008101851852
        ),
    ],
)
def test_change_frequency(change_events, duration, expected):
    """
    Test the change_frequency function with a variety of inputs.
    """
    assert change_frequency(change_events, duration) == pytest.approx(expected)


def test_change_frequency_zero_duration():
    """
    Test that change_frequency raises an InvalidArgument exception for zero duration.
    """
    with pytest.raises(ValueError, match="Duration cannot be zero."):
        change_frequency([], timedelta(days=0))


@pytest.mark.parametrize(
    "change_events, expected",
    [
        # All changes fail (failure rate = 1)
        (
            [
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=False, lead_time=timedelta(seconds=3600)),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 2, 12, 0, 0), success=False, lead_time=timedelta(seconds=7200)),
            ],
            1.0
        ),

        # Half of the changes fail (failure rate = 0.5)
        (
            [
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=False, lead_time=timedelta(seconds=3600)),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 2, 12, 0, 0), success=True, lead_time=timedelta(seconds=7200)),
            ],
            0.5
        ),

        # 42% of the changes fail (failure rate ≈ 0.42)
        (
            [
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=False, lead_time=timedelta(seconds=3600)),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 2, 12, 0, 0), success=True, lead_time=timedelta(seconds=7200)),
                ChangeEvent(identifier="3", stamp=datetime(2023, 1, 3, 12, 0, 0), success=False, lead_time=timedelta(seconds=1800)),
                ChangeEvent(identifier="4", stamp=datetime(2023, 1, 4, 12, 0, 0), success=True, lead_time=timedelta(seconds=4500)),
                ChangeEvent(identifier="5", stamp=datetime(2023, 1, 5, 12, 0, 0), success=False, lead_time=timedelta(seconds=5400)),
                ChangeEvent(identifier="6", stamp=datetime(2023, 1, 6, 12, 0, 0), success=True, lead_time=timedelta(seconds=3600)),
                ChangeEvent(identifier="7", stamp=datetime(2023, 1, 7, 12, 0, 0), success=True, lead_time=timedelta(seconds=7200)),
            ],
            0.42
        ),

        # No failures (failure rate = 0)
        (
            [
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=True, lead_time=timedelta(seconds=3600)),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 2, 12, 0, 0), success=True, lead_time=timedelta(seconds=7200)),
            ],
            0.0
        ),
    ],
)
def test_change_failure_rate(change_events, expected):
    """
    Test the change_failure_rate function with a variety of inputs.
    """
    assert change_failure_rate(change_events) == pytest.approx(expected)