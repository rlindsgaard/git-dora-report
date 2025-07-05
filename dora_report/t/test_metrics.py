import pytest
from datetime import datetime, timedelta
from dora_report.models import ChangeEvent
from dora_report.metrics import (
    change_frequency, 
    change_failure_rate,
    mean_time_to_recover,
    lead_time_for_changes,
)
from faker import Faker

@pytest.fixture
def change_event_factory():
    """
    A pytest fixture for generating a ChangeEvent factory with consecutive timestamps.
    """
    fake = Faker()
    base_time = fake.date_time_this_year()  # Start with a random timestamp

    def factory(success: bool, increment_seconds: int = 300):
        nonlocal base_time
        event = ChangeEvent(
            identifier=fake.uuid4(),
            stamp=base_time,
            success=success,
        )
        base_time += timedelta(seconds=increment_seconds)  # Increment timestamp
        return event

    return factory


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
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=False),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 2, 12, 0, 0), success=False),
            ],
            1.0
        ),

        # Half of the changes fail (failure rate = 0.5)
        (
            [
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=False),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 2, 12, 0, 0), success=True),
            ],
            0.5
        ),

        # 42% of the changes fail (failure rate ≈ 0.42)
        (
            [
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=False),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 2, 12, 0, 0), success=True),
                ChangeEvent(identifier="3", stamp=datetime(2023, 1, 3, 12, 0, 0), success=False),
                ChangeEvent(identifier="4", stamp=datetime(2023, 1, 4, 12, 0, 0), success=True),
                ChangeEvent(identifier="5", stamp=datetime(2023, 1, 5, 12, 0, 0), success=False),
                ChangeEvent(identifier="6", stamp=datetime(2023, 1, 6, 12, 0, 0), success=True),
                ChangeEvent(identifier="7", stamp=datetime(2023, 1, 7, 12, 0, 0), success=True),
            ],
            0.42857142
        ),

        # No failures (failure rate = 0)
        (
            [
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=True),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 2, 12, 0, 0), success=True),
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

@pytest.mark.parametrize(
    "change_events, expected_mean_recovery_time",
    [
        # Case with None values
        (
            [
                ChangeEvent("1", datetime(2023, 1, 1, 12, 0, 0), None),
                ChangeEvent("2", datetime(2023, 1, 1, 12, 10, 0), False),
                ChangeEvent("3", datetime(2023, 1, 1, 12, 20, 0), True),
            ],
            timedelta(minutes=10),
        ),
        # Case 1: All events are successful (MTTR = 0)
        (
            [
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=True),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 2, 12, 0, 0), success=True),
            ],
            timedelta(0),
        ),

        # Case 2: Mean recovery time of 15 minutes
        (
            [
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=True),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 1, 12, 5, 0), success=False),
                ChangeEvent(identifier="3", stamp=datetime(2023, 1, 1, 12, 20, 0), success=True),
                ChangeEvent(identifier="4", stamp=datetime(2023, 1, 1, 12, 25, 0), success=False),
                ChangeEvent(identifier="5", stamp=datetime(2023, 1, 1, 12, 40, 0), success=True),
            ],
            timedelta(minutes=15),
        ),

        # Case 3: No events are successful (MTTR = 0)
        (
            [
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=False),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 1, 12, 10, 0), success=False),
            ],
            timedelta(0),
        ),

        # Case 4: Mean recovery time with failing change events at the end
        (
            [
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=True),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 1, 12, 10, 0), success=False),
                ChangeEvent(identifier="3", stamp=datetime(2023, 1, 1, 12, 20, 0), success=True),
                ChangeEvent(identifier="4", stamp=datetime(2023, 1, 1, 12, 30, 0), success=False),
                ChangeEvent(identifier="5", stamp=datetime(2023, 1, 1, 12, 40, 0), success=False),
            ],
            timedelta(minutes=10),
        ),
    ],
)
def test_mean_time_to_recover(change_events, expected_mean_recovery_time):
    """
    Test the mean_time_to_recover function with various scenarios.
    """
    assert mean_time_to_recover(change_events) == expected_mean_recovery_time
  
@pytest.mark.parametrize(
    "change_events, expected_mean_lead_time",
    [
        # Case with None values
        (
            [
                ChangeEvent(
                    identifier="1", 
                    stamp=datetime(2023, 1, 1, 12, 0, 0), 
                    success=None
                ),
                ChangeEvent(
                    identifier="2", 
                    stamp=datetime(2023, 1, 1, 12, 30, 0), 
                    success=False
                ),
                ChangeEvent(
                    identifier="3", 
                    stamp=datetime(2023, 1, 1, 13, 0, 0), 
                    success=True
                ),
            ],
            timedelta(minutes=30),
        ),
        # Case 1: No succeeding changes (all failures, mean = 0)
        (
            [
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=False),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 1, 12, 30, 0), success=False),
            ],
            timedelta(0),
        ),

        # Case 2: Multiple consecutive successes (mean = 0 because no failures in chunks)
        (
            [
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=True),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 1, 12, 30, 0), success=True),
            ],
            timedelta(seconds=1800),
        ),

        # Case 3: Multiple failures between successes
        (
            [
                ChangeEvent(identifier="1", stamp=datetime(2023, 1, 1, 12, 0, 0), success=False),
                ChangeEvent(identifier="2", stamp=datetime(2023, 1, 1, 12, 30, 0), success=False),
                ChangeEvent(identifier="3", stamp=datetime(2023, 1, 1, 13, 0, 0), success=True),
                ChangeEvent(identifier="4", stamp=datetime(2023, 1, 1, 13, 30, 0), success=False),
                ChangeEvent(identifier="5", stamp=datetime(2023, 1, 1, 14, 0, 0), success=True),
            ],
            timedelta(minutes=45),  # Mean: (60 + 30) / 2 = 45 minutes
        ),
    ],
)
def test_lead_time_for_changes(change_events, expected_mean_lead_time):
    """
    Test the lead_time_for_changes function with various scenarios.
    """
    assert lead_time_for_changes(change_events) == expected_mean_lead_time
    

def test_lead_time_for_changes_with_fixture(change_event_factory):
    """
    Test the lead_time_for_changes function using a ChangeEvent factory.
    """
    # Generate test data using the factory
    change_events = [
        change_event_factory(success=False, increment_seconds=300),  # Event 1 (failure, +5 mins)
        change_event_factory(success=False, increment_seconds=300),  # Event 2 (failure, +5 mins)
        change_event_factory(success=True, increment_seconds=300),   # Event 3 (success, +5 mins)
        change_event_factory(success=False, increment_seconds=300),  # Event 4 (failure, +5 mins)
        change_event_factory(success=True, increment_seconds=300),   # Event 5 (success, +5 mins)
    ]

    # Calculate expected lead times:
    # Chunk 1: Lead times = (T3-T1) and (T3-T2)
    # Chunk 2: Lead time  = (T5-T4)
    lead_time_chunk_1 = timedelta(seconds=300 + 300)  # 10 minutes
    lead_time_chunk_2 = timedelta(seconds=300)        # 5 minutes
    expected_mean_lead_time = (lead_time_chunk_1 + lead_time_chunk_2) / 2

    # Assert the result
    assert lead_time_for_changes(change_events) == expected_mean_lead_time 
