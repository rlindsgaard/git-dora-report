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


def mean_time_to_recover(change_events: list[ChangeEvent]) -> timedelta:
    """
    Calculate the mean time to recover (MTTR) from failures.

    :param change_events: A list of ChangeEvent objects.
    :type change_events: list[ChangeEvent]
    :return: The mean time to recover (average recovery time across all failures).
    :rtype: timedelta
    """
    if not change_events:
        return timedelta(0)

    recovery_times = []
    failure_start = None  # Tracks the start of a failure

    # Iterate over events to calculate recovery times
    for event in change_events:
        if not event.success:
            if failure_start is None:
                failure_start = event.stamp  # Mark the start of failure
        elif failure_start:
            # Recovery happens at the first successful event after a failure
            recovery_time = event.stamp - failure_start
            recovery_times.append(recovery_time)
            failure_start = None  # Reset failure start

    # If failures end without recovery, do not count them in MTTR
    if not recovery_times:
        return timedelta(0)

    # Calculate the mean recovery time
    return sum(recovery_times, timedelta(0)) / len(recovery_times)