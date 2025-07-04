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
                    id="1", 
                    stamp=datetime(2023, 1, 1, 12, 0, 0), 
                    success=True,
                    lead_time=timedelta(seconds=3600)
                )
            ], 
            timedelta(days=7), 
            0.00000165344
        ),
        (
            [ChangeEvent(id="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=True, lead_time=timedelta(seconds=3600))], timedelta(days=1), 0.0000115741),

        # Seven ChangeEvents
        ([ChangeEvent(id=str(i), stamp=datetime(2023, 1, 1, 12, 0, 0), success=True, lead_time=timedelta(seconds=3600)) for i in range(7)], timedelta(days=7), 7 / (7 * 86400)),
        ([ChangeEvent(id=str(i), stamp=datetime(2023, 1, 1, 12, 0, 0), success=True, lead_time=timedelta(seconds=3600)) for i in range(7)], timedelta(days=1), 0.0000810185),
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