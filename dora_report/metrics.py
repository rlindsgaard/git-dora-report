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