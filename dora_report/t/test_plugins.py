import pytest
from datetime import datetime, timedelta
from argparse import Namespace
from dora_report.plugins import GitMergeWithTag
from dora_report.models import ChangeEvent

def test_acquire_change_events():
    """
    Test the acquire_change_events method of the GitMergeWithTag class.
    """
    # Define the arguments with a time range
    arguments = Namespace(
        since=datetime(2023, 1, 1, 12, 0, 0),
        until=datetime(2023, 1, 1, 13, 0, 0)
    )

    # Call the static method directly
    events = list(GitMergeWithTag.acquire_change_events(arguments))

    # Assertions
    assert len(events) > 0, "The generator did not yield any ChangeEvent objects."

    for event in events:
        assert isinstance(event, ChangeEvent), "Yielded object is not a ChangeEvent."
        assert arguments.since <= event.stamp <= arguments.until, "Event stamp is outside the specified time range."

    # Ensure timestamps are incremental
    for i in range(len(events) - 1):
        assert events[i].stamp < events[i + 1].stamp, "Timestamps are not incremental."

def test_acquire_change_events_invalid_arguments():
    """
    Test that acquire_change_events raises an error if arguments are missing required attributes.
    """
    # Invalid arguments (missing 'since' and 'until')
    invalid_arguments = Namespace()

    with pytest.raises(ValueError, match="Arguments object must have 'since' and 'until' attributes."):
        list(GitMergeWithTag.acquire_change_events(invalid_arguments))