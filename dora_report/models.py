from pydantic import BaseModel
from datetime import datetime, timedelta

class ChangeEvent(BaseModel):
    """
    Represents a change event with associated metadata and metrics.

    :param identifier: A unique identifier for the change event.
    :type identifier: str
    :param stamp: The timestamp of when the event occurred.
    :type stamp: datetime
    :param success: Indicates whether the change was successful. 
                    ``True`` means success, ``False`` indicates an error.
    :type success: bool
    :param lead_time: The time between when work started and when the change 
                      was registered, measured in seconds.
    :type lead_time: timedelta
    """
    identifier: str
    stamp: datetime
    success: bool
    lead_time: timedelta