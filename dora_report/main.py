from argparse import ArgumentParser
from datetime import datetime, timedelta
import logging

from dora_report.plugins import FakeGitMerge


class DoraReport:
    def __init__(self, args):
        self.collector = args.collector
        self.interval_seconds = args.interval_seconds
        self.since = args.since_dt
        self.until = args.until_dt
        self.records = []
        
    def analyze(self):
        event_gen = self.collector.collect_change_events()
        for chunk in chunk_interval(event_gen, start=self.since, size=self.interval_seconds, end=self.until):
            # Aggregate
            record = Record(
                start=chunk["start"],
                end=chunk["end"],
                duration=chunk["duration"],
            ) 
            self.records.append(record)

 
class Record:
    def __init__(self, start, end, duration):
        self.fields = {
            "start": start,
            "end": end,
            "duration": duration
        }


def main():
    collectors = {}
    parser = ArgumentParser()
    
    # Add subcommand
    subparsers = parser.add_subparsers(
        dest="collector_name", 
        help="subcommand help",
    )
    p1 = subparsers.add_parser(FakeGitMerge.name)
    FakeGitMerge.add_arguments(p1)
    collectors[FakeGitMerge.name] = FakeGitMerge
    
    # Add root-level arguments
    parser.add_argument(
        "--since",
        required=False,
        default=None,
        help='Start date (e.g., "2024-01-01"). Defaults to the beginning of history.',  # noqa: E501
    )
    parser.add_argument(
        "--until",
        required=False,
        default=None,
        help='End date (e.g., "2024-12-31"). Defaults to now.',  # noqa: E501
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase output verbosity (repeat for more)",  # noqa: E501
    )
    parser.add_argument(
        "--interval",
        required=False,
        default="1m",
        help="Interval size (e.g., 7d, 1w, 1m)",  # noqa: E501
    )
    
    args = parser.parse_args()
 
    log = setup_logging(args.verbose)
    args.log = log
    
    # Parse date arguments
    if not args.until:
        until_dt = datetime.now()
    else:
        until_dt = (
            datetime.strptime(args.until, "%Y-%m-%dT%H:%M:%S")
            if "T" in args.until
            else datetime.strptime(args.until, "%Y-%m-%d")
        )
    if not args.since:
        since_dt = datetime(1970, 1, 1)
        log.warning(
            "No --since provided, defaulting to start of Unix epoch (1970-01-01 00:00:00)."
        )
    else:
        since_dt = (
            datetime.strptime(args.since, "%Y-%m-%dT%H:%M:%S")
            if "T" in args.since
            else datetime.strptime(args.since, "%Y-%m-%d")
        )

    interval_seconds = parse_interval(args.interval)

    args.since_dt = since_dt
    args.until_dt = until_dt
    args.interval_seconds = interval_seconds
      
    print(args)
    collector = collectors[args.collector_name].from_arguments(args)
    args.collector = collector
    report = DoraReport(args)
    report.analyze()


def setup_logging(verbosity: int) -> logging.Logger:
    """Set up logging based on verbosity level."""
    log_level = logging.WARNING
    if verbosity == 1:
        log_level = logging.INFO
    elif verbosity >= 2:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s")
    log = logging.getLogger("dora-metrics")
    log.info(f"Verbosity set to {verbosity}")
    return log 


def parse_interval(interval_str):
    """
    Parse interval string into seconds
    """
    if interval_str.endswith("d"):
        return int(interval_str[:-1]) * 86400.0 # Days
    elif interval_str.endswith("w"):
        return int(interval_str[:-1]) * 604800.0  # Weeks converted to days
    elif interval_str.endswith("m"):
        return int(interval_str[:-1]) *   2592000.0 # Approximate months as 30 days
    else:
        raise ValueError("Invalid interval format. Use Nd, Nw, or Nm (e.g., 7d, 2w, 1m)")


def chunk_interval(event_gen, since, size, until):
      
    def interval_gen(start, stop, step):
        start_dt = start
        end_dt = start_dt + step
        duration = (end_dt - start_dt).total_seconds()
        while end_dt < stop:
            yield start_dt, end_dt, duration
            start_dt = end_dt
            end_dt = end_dt + step
            duration = (end_dt - start_dt).total_seconds()
        yield start_dt, stop, duration
     
    intervals = interval_gen(
        since, 
        until, 
        timedelta(seconds=size),
    ) 

    def chunk_events(start, stop):
        chunk = []
        last_failure = None
        for event in event_gen:
            if event.stamp > e: 
                yield chunk, last_failure
                chunk = [] 
            if event.success:
                last_failure = None
            elif event.success is False and  last_failure is None:
                last_failure = event.stamp     
            chunk.append(event)
        yield chunk, last_failure 

    for s, e, d in intervals:
        chunk, last_failure = chunk_events(s, e)
        yield {
            "start": s,
            "end": e,
            "duration": d,
            "last_failure": last_failure,
            "events": chunk,
        }

           
if __name__ == "__main__":
    main()
 