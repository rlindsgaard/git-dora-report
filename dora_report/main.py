from argparse import ArgumentParser
from datetime import datetime, timedelta
import logging

from dora_report.plugins import FakeGitMerge


class DoraReport:
    def __init__(self, collector):
        self.collector = collector

def main():
    collectors = {}
    parser = ArgumentParser()
    
    # Add subcommand
    subparsers = parser.add_subparsers(
        dest="collector", 
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
    collector = collectors[args.collector].from_arguments(args)
    DoraReport(collector=collector)

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


def chunk_interval(event_gen, start, size, end):
    start_dt = start
    end_dt = start_dt + timedelta(seconds=size)
    
    def next_end():
        ret = start_dt + timedelta(seconds=size)
        if end_dt > end:
            return end
        return ret 
 
    end_dt = next_end()
    last_failure = None
    
    for event in event_gen:
        if event.success:
            last_failure = None
        elif event.success is False:
            last_failure = event.stamp  
  
        if event.stamp > end_dt:
            yield {
                "start": start_dt,
                "end": end_dt,
                "duration": (start_dt - end_dt).seconds,
                "last_failure": last_failure,
                "events": chunk,
            }
            # Setup new chunk
            start_dt = end_dt
            end_dt = next_end()
                
            chunk = []
        chunk.append(event)
           
if __name__ == "__main__":
    main()
 