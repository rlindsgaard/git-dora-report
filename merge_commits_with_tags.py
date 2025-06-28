import subprocess
import argparse
import re
from typing import List, Dict

def get_merge_commits(repo_path: str, since: str, until: str) -> List[Dict]:
    # Get merge commits with timestamps and tags
    git_log_cmd = [
        'git', '-C', repo_path, 'log', '--merges', '--pretty=format:%H|%ct|%s'
    ]
    if since:
        git_log_cmd.append(f'--since={since}')
    if until:
        git_log_cmd.append(f'--until={until}')
    result = subprocess.run(git_log_cmd, capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    merge_commits = []
    for line in lines:
        if not line:
            continue
        commit_hash, timestamp, subject = line.split('|', 2)
        tags = get_tags_for_commit(repo_path, commit_hash)
        merge_commits.append({
            'hash': commit_hash,
            'timestamp': int(timestamp),
            'tags': tags,
            'subject': subject
        })
    return merge_commits

def get_tags_for_commit(repo_path: str, commit_hash: str) -> List[str]:
    git_tag_cmd = [
        'git', '-C', repo_path, 'tag', '--points-at', commit_hash
    ]
    result = subprocess.run(git_tag_cmd, capture_output=True, text=True)
    tags = result.stdout.strip().split('\n') if result.stdout.strip() else []
    return tags

def main():
    parser = argparse.ArgumentParser(description='List merge commits with timestamps and tags in a git repo.')
    parser.add_argument('repo', help='Path to the git repository')
    parser.add_argument('--since', required=False, default=None, help='Start date (e.g., "2024-01-01"). Defaults to the beginning of history.')
    parser.add_argument('--until', required=False, default=None, help='End date (e.g., "2024-12-31"). Defaults to now.')
    args = parser.parse_args()

    since = args.since if args.since else ''
    if not args.until:
        from datetime import datetime
        until = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    else:
        until = args.until

    merges = get_merge_commits(args.repo, since, until)
    for m in merges:
        print(f"{m['hash']} | {m['timestamp']} | {', '.join(m['tags'])} | {m['subject']}")

if __name__ == '__main__':
    main()
