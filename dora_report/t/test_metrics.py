import pytest
from datetime import datetime, timedelta
from dora_report.models import ChangeEvent
from dora_report.metrics import change_frequency

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