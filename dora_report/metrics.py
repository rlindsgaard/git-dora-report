from datetime import timedelta
from dora_report.models import ChangeEvent

def change_frequency(change_events: list[ChangeEvent], duration: timedelta) -> float:
    """
    Calculate the frequency of changes.

    :param change_events: A list of ChangeEvent objects.
    :type change_events: list[ChangeEvent]
    :param duration: A timedelta representing the duration.
    :type duration: timedelta
    :return: The change frequency (number of events divided by total seconds of the duration).
    :rtype: float
    :raises InvalidArgument: If the duration has zero seconds.
    """
    if duration.total_seconds() == 0:
        raise ValueError("Duration cannot be zero.")

    return len(change_events) / duration.total_seconds()


def change_failure_rate(change_events: list[ChangeEvent]) -> float:
    """
    Calculate the change failure rate.

    :param change_events: A list of ChangeEvent objects.
    :type change_events: list[ChangeEvent]
    :return: The failure rate (number of failed changes divided by total changes).
    :rtype: float
    """
    if not change_events:
        return 0.0

    total_events = len(change_events)
    failed_events = sum(1 for event in change_events if not event.success)

    return failed_events / total_events 