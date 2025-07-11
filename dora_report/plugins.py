from datetime import datetime, timedelta
from typing import Generator
from argparse import Namespace
from faker import Faker
from dora_report.models import ChangeEvent
import os

class FakeGitMerge:
    """
    A plugin to acquire change events within a specified time range.
    """
    def __init__(self, log, since, until):
        self.log = log
        self.since = since
        self.until = until
 
    @classmethod
    def from_arguments(cls, arguments):
        # Ensure the arguments have the required attributes
        if not hasattr(arguments, "since_dt") or not hasattr(arguments, "until_dt"):
            raise ValueError(
                "Arguments object must have 'since' and 'until' attributes."
            )
        obj = cls(
            arguments.log,
            arguments.since_dt, 
            arguments.until_dt,
        )
        return obj
        
    @staticmethod
    def add_arguments(parser):
        """
        Add plugin centric arguments
        
        The plugin's behavior can be modified at runtime with the
        arguments added to the parser.
        Command line options are made available to the plugin via 
        the arguments parameter in the `from_arguments` method.
        """
        pass
                     
 
    def collect_change_events(self) -> Generator[ChangeEvent, None, None]:
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

        current_time = self.since

        # Generate events until the current_time exceeds 'until'
        while current_time < arguments.until:
            self.log.info("Generating a new ChangeEvent")
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
                success=fake.random_element([True, False, None]),
            )