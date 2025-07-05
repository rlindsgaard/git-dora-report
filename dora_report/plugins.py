from datetime import datetime, timedelta
from typing import Generator
from argparse import Namespace
from faker import Faker
from dora_report.models import ChangeEvent

class GitMergeWithTag:
    """
    A plugin to acquire change events within a specified time range.
    """

    @staticmethod
    def acquire_change_events(arguments: Namespace) -> Generator[ChangeEvent, None, None]:
        """
        A generator method that yields ChangeEvent objects with stamps within the
        time range specified by the arguments object.

        :param arguments: An object containing 'since' and 'until' datetime attributes
                          that define the time range.
        :type arguments: Namespace
        :yield: ChangeEvent objects with incrementally generated stamps and varying
                success values.
        :rtype: Generator[ChangeEvent, None, None]
        """
        fake = Faker()

        # Ensure the arguments have the required attributes
        if not hasattr(arguments, "since") or not hasattr(arguments, "until"):
            raise ValueError("Arguments object must have 'since' and 'until' attributes.")

        current_time = arguments.since

        # Generate events until the current_time exceeds 'until'
        while current_time < arguments.until:
            # Generate a random increment (e.g., 1-10 minutes)
            increment = timedelta(minutes=fake.random_int(min=1, max=10))
            current_time += increment

            # If current time exceeds the 'until' range, stop generation
            if current_time > arguments.until:
                break

            # Yield a ChangeEvent with varying success
            yield ChangeEvent(
                identifier=fake.sha1(),
                stamp=current_time,
                success=fake.boolean(),
                lead_time=timedelta(seconds=fake.random_int(min=0, max=3600)),
            )