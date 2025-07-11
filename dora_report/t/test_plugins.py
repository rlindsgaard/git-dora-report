import pytest
from datetime import datetime, timedelta
from argparse import Namespace
from dora_report.plugins import FakeGitMerge
from dora_report.models import ChangeEvent
import subprocess

@pytest.fixture
def plugin_factory(root_logger, tmp_path):
    def inner(
        logger=root_logger,
        repository=tmp_path
        since=datetime(2023, 1, 1, 12, 0, 0),
        until=datetime(2023, 1, 1, 13, 0, 0),
    ):
        arguments = Namespace(
            log=logger,
            repository=repository,
            since,
            until
        )

        return FakeGitMerge.from_arguments(arguments)
    return inner

def test_collect_change_events(plugin_factory):
    """
    Test the acquire_change_events method of the GitMergeWithTag class.
    """
    example_plugin = plugin_factory()
    
    # Call the static method directly
    events = list(example_plugin.collect_change_events(arguments))

    # Assertions
    assert len(events) > 0, "The generator did not yield any ChangeEvent objects."

    for event in events:
        assert isinstance(event, ChangeEvent), "Yielded object is not a ChangeEvent."
        assert arguments.since <= event.stamp <= arguments.until, "Event stamp is outside the specified time range."

    # Ensure timestamps are incremental
    for i in range(len(events) - 1):
        assert events[i].stamp < events[i + 1].stamp, "Timestamps are not incremental."


def test_collect_change_events_invalid_arguments(plugin_factory):
    """
    Test that object instantiation raises an error if arguments are missing required attributes.
    """
    # Invalid arguments (missing 'since' and 'until')

    with pytest.raises(ValueError, match="Arguments object must have 'since' and 'until' attributes."):
        arguments = Namespace()
        FakeGitMerge.from_arguments(arguments)