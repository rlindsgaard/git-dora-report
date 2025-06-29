import subprocess
import argparse
import fnmatch
import statistics
import logging
import csv
from typing import List, Dict
from datetime import datetime, timedelta

def get_merge_commits(repo_path: str, since: str, until: str, tag_pattern: str = None, branch: str = None, log=None) -> List[Dict]:
    if log:
        log.debug(f"Getting merge commits in {repo_path} branch={branch} since={since} until={until} tag_pattern={tag_pattern}")
    git_log_cmd = [
        'git', '-C', repo_path, 'log', '--merges', '--pretty=format:%H|%ct|%s', '--reverse'
    ]
    if branch:
        git_log_cmd.append(branch)
    if since:
        git_log_cmd.append(f'--since={since}')
    if until:
        git_log_cmd.append(f'--until={until}')
    if log:
        log.debug(f"Running git log command: {' '.join(git_log_cmd)}")
    result = subprocess.run(git_log_cmd, capture_output=True, text=True)
    if log and result.stderr:
        log.warning(f"git log stderr: {result.stderr}")
    lines = result.stdout.strip().split('\n')
    merge_commits = []
    for line in lines:
        if not line:
            continue
        try:
            commit_hash, timestamp, subject = line.split('|', 2)
        except Exception as e:
            if log:
                log.error(f"Failed to parse line: {line} ({e})")
            continue
        tags = get_tags_for_commit(repo_path, commit_hash, log=log)
        if tag_pattern:
            tags = [tag for tag in tags if fnmatch.fnmatch(tag, tag_pattern)]
        merge_commits.append({
            'hash': commit_hash,
            'timestamp': int(timestamp),
            'tags': tags,
            'subject': subject
        })
    if log:
        log.debug(f"Found {len(merge_commits)} merge commits")
    return merge_commits

def get_tags_for_commit(repo_path: str, commit_hash: str, log=None) -> List[str]:
    git_tag_cmd = [
        'git', '-C', repo_path, 'tag', '--points-at', commit_hash
    ]
    if log:
        log.debug(f"Running git tag command: {' '.join(git_tag_cmd)}")
    result = subprocess.run(git_tag_cmd, capture_output=True, text=True)
    if log and result.stderr:
        log.warning(f"git tag stderr: {result.stderr}")
    tags = result.stdout.strip().split('\n') if result.stdout.strip() else []
    if log:
        log.debug(f"Tags for {commit_hash}: {tags}")
    return tags

def classify_tag_state(tags: list, tag_pattern: str, prev_state: str = None) -> str:
    """
    Classifies the state for a tag pattern as 'success', 'failed', or 'recovery'.
    - 'success': tag matching pattern is present
    - 'failed': tag matching pattern is not present
    - 'recovery': previous was 'failed' or None, now 'success'
    """
    matched = any(fnmatch.fnmatch(tag, tag_pattern) for tag in tags)
    if matched:
        if prev_state in [None, 'failed']:
            return 'recovery'
        else:
            return 'success'
    else:
        return 'failed'

def get_first_commit_time_of_branch(repo_path: str, merge_commit_hash: str, log=None) -> int:
    # Get the second parent (feature branch tip) of the merge commit
    cmd = ['git', '-C', repo_path, 'rev-list', '--parents', '-n', '1', merge_commit_hash]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if log:
            log.error(f"Failed to get parents for {merge_commit_hash}: {result.stderr}")
        return None
    parts = result.stdout.strip().split()
    if len(parts) < 3:
        if log:
            log.warning(f"Merge commit {merge_commit_hash} does not have two parents")
        return None
    feature_branch_tip = parts[2]
    # Find the root commit of the feature branch (not reachable from the first parent)
    cmd = [
        'git', '-C', repo_path, 'rev-list', '--reverse', feature_branch_tip, f'^{parts[1]}'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        if log:
            log.error(f"Failed to get root commit for branch tip {feature_branch_tip}: {result.stderr}")
        return None
    root_commit = result.stdout.strip().split('\n')[0]
    # Get the commit time of the root commit
    cmd = ['git', '-C', repo_path, 'show', '-s', '--format=%ct', root_commit]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if log:
            log.error(f"Failed to get commit time for {root_commit}: {result.stderr}")
        return None
    return int(result.stdout.strip())

def parse_interval(interval_str):
    if interval_str.endswith('d'):
        return timedelta(days=int(interval_str[:-1]))
    elif interval_str.endswith('w'):
        return timedelta(weeks=int(interval_str[:-1]))
    elif interval_str.endswith('m'):
        # Approximate a month as 30 days
        return timedelta(days=30*int(interval_str[:-1]))
    else:
        raise ValueError('Invalid interval format. Use Nd, Nw, or Nm (e.g., 7d, 2w, 1m)')

def dora_metrics_for_range(repo, tag, branch, since, until, log):
    merges = get_merge_commits(repo, since, until, tag, branch, log=log)
    prev_state = 'failed'
    states = []
    times = []
    last_success_time = None
    last_failed_time = None
    recovery_times = []
    lead_times = []
    for m in merges:
        state = classify_tag_state(m['tags'], tag, prev_state)
        # Lead time calculation
        first_commit_time = get_first_commit_time_of_branch(repo, m['hash'], log=log)
        if first_commit_time:
            lead_time = m['timestamp'] - first_commit_time
            lead_times.append(lead_time)
        states.append(state)
        if state in ['success', 'recovery']:
            times.append(m['timestamp'])
        if state == 'recovery' and last_failed_time:
            recovery_times.append(m['timestamp'] - last_failed_time)
        if state == 'failed':
            last_failed_time = m['timestamp']
        if state in ['success', 'recovery']:
            last_success_time = m['timestamp']
        prev_state = state if state != 'recovery' else 'success'
    deployment_count = states.count('success') + states.count('recovery')
    total_merges = len(states)
    change_failure_count = states.count('failed')
    deployment_frequency = deployment_count / ((times[-1] - times[0]) / 86400) if len(times) > 1 else deployment_count
    change_failure_rate = change_failure_count / total_merges if total_merges else 0
    mttr = statistics.mean(recovery_times) if recovery_times else 0
    mean_lead_time = statistics.mean(lead_times) if lead_times else 0
    return {
        'deployment_frequency': deployment_frequency,
        'change_failure_rate': change_failure_rate,
        'mttr': mttr,
        'mean_lead_time': mean_lead_time,
        'deployment_count': deployment_count,
        'total_merges': total_merges
    }

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Generate DORA metrics from merge commits in a git repo.')
    parser.add_argument('repo', help='Path to the git repository')
    parser.add_argument('--since', required=False, default=None, help='Start date (e.g., "2024-01-01"). Defaults to the beginning of history.')
    parser.add_argument('--until', required=False, default=None, help='End date (e.g., "2024-12-31"). Defaults to now.')
    parser.add_argument('--tag', required=True, help='Tag pattern to classify (e.g., "build-*")')
    parser.add_argument('--branch', required=False, default=None, help='Branch to scan (e.g., "main" or "master")')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase output verbosity (repeat for more)')
    parser.add_argument('--interval', required=False, default=None, help='Interval size (e.g., 7d, 1w, 1m)')
    parser.add_argument('--count', required=False, type=int, default=None, help='Number of intervals')
    parser.add_argument('--csv', required=False, default=None, help='CSV output file')
    parser.add_argument('--ma', required=False, type=int, default=3, help='Moving average window (number of intervals, default 3, simple)')
    return parser.parse_args()

def setup_logging(verbosity: int) -> logging.Logger:
    """Set up logging based on verbosity level."""
    log_level = logging.WARNING
    if verbosity == 1:
        log_level = logging.INFO
    elif verbosity >= 2:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level, format='[%(levelname)s] %(message)s')
    log = logging.getLogger("dora-metrics")
    log.info(f"Verbosity set to {verbosity}")
    return log

def generate_intervals(since_dt, until_dt, interval_td, count, log):
    """Generate a list of (interval_start, interval_end) tuples for reporting."""
    intervals = []
    for i in range(count):
        interval_end = until_dt - i * interval_td
        interval_start = interval_end - interval_td
        if interval_start < since_dt:
            log.info(f"Stopping interval generation: interval_start {interval_start} < since {since_dt}")
            break
        intervals.append((interval_start, interval_end))
    intervals.reverse()  # earliest interval first
    return intervals

def write_csv_report(results, csv_file, ma_fields, ma_fieldnames):
    """Write the DORA metrics and moving averages to a CSV file."""
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'interval_start', 'interval_end',
            'deployment_frequency', 'change_failure_rate', 'mttr', 'mean_lead_time', 'deployment_count', 'total_merges',
            *ma_fieldnames
        ])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

def main():
    """Main entry point for DORA metrics reporting."""
    args = parse_args()
    log = setup_logging(args.verbose)
    print(args)

    # Parse date arguments
    if not args.until:
        until_dt = datetime.now()
    else:
        until_dt = datetime.strptime(args.until, '%Y-%m-%dT%H:%M:%S') if 'T' in args.until else datetime.strptime(args.until, '%Y-%m-%d')
    if not args.since:
        # Find the timestamp of the first commit in the repo
        cmd = ['git', '-C', args.repo, 'rev-list', '--max-parents=0', '--reverse', '--timestamp', 'HEAD']
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            first_line = result.stdout.strip().split('\n')[0]
            first_timestamp = int(first_line.split()[0])
            since_dt = datetime.fromtimestamp(first_timestamp)
            log.info(f"No --since provided, using timestamp of first commit: {since_dt}")
        else:
            since_dt = datetime(1970, 1, 1)
            log.warning("No --since provided and could not determine first commit, defaulting to start of Unix epoch (1970-01-01 00:00:00).")
    else:
        since_dt = datetime.strptime(args.since, '%Y-%m-%dT%H:%M:%S') if 'T' in args.since else datetime.strptime(args.since, '%Y-%m-%d')

    # Determine interval size
    if not args.interval:
        interval_td = until_dt - since_dt
        args.interval = f"{interval_td.days}d"
        log.info(f"Defaulting interval to {args.interval} based on --since and --until")
    else:
        interval_td = parse_interval(args.interval)
    if not args.count:
        args.count = 1

    # Generate intervals
    intervals = generate_intervals(since_dt, until_dt, interval_td, args.count, log)

    # Collect metrics for each interval
    results = []
    for interval_start, interval_end in intervals:
        since_str = interval_start.strftime('%Y-%m-%dT%H:%M:%S')
        until_str = interval_end.strftime('%Y-%m-%dT%H:%M:%S')
        log.info(f"Collecting metrics for interval {since_str} to {until_str}")
        metrics = dora_metrics_for_range(args.repo, args.tag, args.branch, since_str, until_str, log)
        results.append({
            'interval_start': since_str,
            'interval_end': until_str,
            **metrics
        })

    # Compute simple moving averages if requested
    ma_fields = ['deployment_frequency', 'change_failure_rate', 'mttr', 'mean_lead_time', 'deployment_count', 'total_merges']
    if args.ma and args.ma > 1:
        for field in ma_fields:
            ma_values = []
            for i in range(len(results)):
                window = results[max(0, i - args.ma + 1):i + 1]
                vals = [row[field] for row in window]
                avg = sum(vals) / len(vals) if vals else 0
                ma_values.append(avg)
            # Add moving average fields to results
            for i in range(len(results)):
                results[i][f'ma_{field}'] = ma_values[i]

    # Write CSV report if requested
    if args.csv:
        write_csv_report(results, args.csv, ma_fields, [f'ma_{field}' for field in ma_fields])

    # Print results to console
    headers = ['Interval Start', 'Interval End', 'Deployment Frequency', 'Change Failure Rate', 'MTTR', 'Mean Lead Time', 'Deployment Count', 'Total Merges']
    ma_headers = [f'MA {field}' for field in ma_fields]
    print(f"{' | '.join(headers + ma_headers)}")
    for row in results:
        print(" | ".join(f"{row[h]:.2f}" if isinstance(row[h], (int, float)) else str(row[h]) for h in headers + ma_headers))

if __name__ == "__main__":
    main()
