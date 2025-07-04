import pytest
from datetime import datetime, timedelta
from dora_report.models import ChangeEvent

def test_change_event_instantiation():
    """
    Test the instantiation of the ChangeEvent class with valid data.
    """
    # Instantiate the ChangeEvent with literal values
    change_event = ChangeEvent(
        id="unique-change-001",
        stamp=datetime(2023, 1, 1, 12, 0, 0),
        success=True,
        lead_time=timedelta(seconds=3600)  # 1 hour
    )

    # Assertions to verify the instantiation
    assert change_event.id == "unique-change-001"
    assert change_event.stamp == datetime(2023, 1, 1, 12, 0, 0)
    assert change_event.success is True
    assert change_event.lead_time == timedelta(seconds=3600)