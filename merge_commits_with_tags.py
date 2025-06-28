import subprocess
import argparse
import re
import fnmatch
import statistics
import logging
from typing import List, Dict

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

def main():
    parser = argparse.ArgumentParser(description='Generate DORA metrics from merge commits in a git repo.')
    parser.add_argument('repo', help='Path to the git repository')
    parser.add_argument('--since', required=False, default=None, help='Start date (e.g., "2024-01-01"). Defaults to the beginning of history.')
    parser.add_argument('--until', required=False, default=None, help='End date (e.g., "2024-12-31"). Defaults to now.')
    parser.add_argument('--tag', required=True, help='Tag pattern to classify (e.g., "build-*")')
    parser.add_argument('--branch', required=False, default=None, help='Branch to scan (e.g., "main" or "master")')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase output verbosity (repeat for more)')
    args = parser.parse_args()

    # Set up logging
    log_level = logging.WARNING
    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose >= 2:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level, format='[%(levelname)s] %(message)s')
    log = logging.getLogger("dora-metrics")
    log.info(f"Verbosity set to {args.verbose}")

    since = args.since if args.since else ''
    if not args.until:
        from datetime import datetime
        until = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    else:
        until = args.until

    merges = get_merge_commits(args.repo, since, until, args.tag, args.branch, log=log)
    prev_state = 'failed'
    states = []
    times = []
    last_success_time = None
    last_failed_time = None
    recovery_times = []
    for m in merges:
        state = classify_tag_state(m['tags'], args.tag, prev_state)
        if log:
            log.debug(f"Commit {m['hash']} tags={m['tags']} state={state}")
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
    # DORA metrics
    deployment_count = states.count('success') + states.count('recovery')
    total_merges = len(states)
    change_failure_count = states.count('failed')
    deployment_frequency = deployment_count / ((times[-1] - times[0]) / 86400) if len(times) > 1 else deployment_count
    change_failure_rate = change_failure_count / total_merges if total_merges else 0
    mttr = statistics.mean(recovery_times) if recovery_times else 0
    print('DORA Metrics Report:')
    print(f'- Deployment Frequency: {deployment_frequency:.2f} per day')
    print(f'- Change Failure Rate: {change_failure_rate:.2%}')
    print(f'- Mean Time to Recovery (MTTR): {mttr/3600:.2f} hours')
    print(f'- Total Deployments: {deployment_count}')
    print(f'- Total Merge Events: {total_merges}')
    # Optionally print lead time for changes if you have commit-to-merge info
    # Print details for each merge
    for m, state in zip(merges, states):
        print(f"{m['hash']} | {m['timestamp']} | {', '.join(m['tags'])} | {state} | {m['subject']}")

if __name__ == '__main__':
    main()
