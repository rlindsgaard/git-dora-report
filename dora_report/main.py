from argparse import ArgumentParser

def main():
    parser = ArgumentParser()
    
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
            "No --since provided and could not determine first commit, defaulting to start of Unix epoch (1970-01-01 00:00:00)."
        )
    else:
        since_dt = (
            datetime.strptime(args.since, "%Y-%m-%dT%H:%M:%S")
            if "T" in args.since
            else datetime.strptime(args.since, "%Y-%m-%d")
        )

    interval_td = parse_interval(args.interval)

    print(args)
 
 
def parse_interval(interval_str):
    if interval_str.endswith("d"):
        return int(interval_str[:-1])  # Days
    elif interval_str.endswith("w"):
        return int(interval_str[:-1]) * 7  # Weeks converted to days
    elif interval_str.endswith("m"):
        return int(interval_str[:-1]) * 30  # Approximate months as 30 days
    else:
        raise ValueError("Invalid interval format. Use Nd, Nw, or Nm (e.g., 7d, 2w, 1m)")


if __name__ == "__main__":
    main()