import os
import subprocess
import tempfile
import shutil
import time
import sys
import logging
import pytest
from merge_commits_with_tags import get_merge_commits, classify_tag_state


@pytest.fixture(autouse=True, scope='session')
def set_debug_logging():
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
    logging.getLogger("dora-metrics").setLevel(logging.DEBUG)


class TestClassifyTagState:
    def test_success(self):
        tags = ['build-123']
        assert classify_tag_state(tags, 'build-*', 'failed') == 'recovery'
        assert classify_tag_state(tags, 'build-*', 'success') == 'success'

    def test_failed(self):
        tags = ['release-123']
        assert classify_tag_state(tags, 'build-*', 'failed') == 'failed'
        assert classify_tag_state(tags, 'build-*', 'success') == 'failed'

    def test_recovery(self):
        tags1 = []
        tags2 = ['build-123']
        state1 = classify_tag_state(tags1, 'build-*', 'failed')
        state2 = classify_tag_state(tags2, 'build-*', state1)
        assert state1 == 'failed'
        assert state2 == 'recovery'

    def test_none_prev_state(self):
        tags1 = []
        tags2 = ['build-123']
        state1 = classify_tag_state(tags1, 'build-*', None)
        state2 = classify_tag_state(tags2, 'build-*', state1)
        assert state1 == 'failed'
        assert state2 == 'recovery'

    def test_multiple_commits(self):
        tags_list = [[], ['build-1'], ['build-2']]
        prev_state = 'failed'
        states = []
        for tags in tags_list:
            state = classify_tag_state(tags, 'build-*', prev_state)
            states.append(state)
            prev_state = state if state != 'recovery' else 'success'
        assert states == ['failed', 'recovery', 'success']

def run_git(cmd, cwd):
    result = subprocess.run(['git'] + cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()

def test_pipeline_tag_classification_integration(tmp_path):
    tempdir = tmp_path
    def run_git(cmd, cwd):
        result = subprocess.run(['git'] + cmd, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{result.stderr}")
        return result.stdout.strip()
    run_git(['init'], tempdir)
    run_git(['config', 'user.email', 'test@example.com'], tempdir)
    run_git(['config', 'user.name', 'Test User'], tempdir)
    with open(tempdir / 'file.txt', 'w') as f:
        f.write('init\n')
    run_git(['add', 'file.txt'], tempdir)
    run_git(['commit', '-m', 'Initial commit'], tempdir)
    # 1st merge: no tag (should be failed)
    run_git(['checkout', '-b', 'feature1'], tempdir)
    with open(tempdir / 'file.txt', 'a') as f:
        f.write('feature1\n')
    run_git(['add', 'file.txt'], tempdir)
    run_git(['commit', '-m', 'Feature 1'], tempdir)
    run_git(['checkout', 'master'], tempdir)
    run_git(['merge', '--no-ff', 'feature1', '-m', 'Merge feature1'], tempdir)
    # 2nd merge: build tag (should be recovery)
    run_git(['checkout', '-b', 'feature2'], tempdir)
    with open(tempdir / 'file2.txt', 'w') as f:
        f.write('feature2\n')
    run_git(['add', 'file2.txt'], tempdir)
    run_git(['commit', '-m', 'Feature 2'], tempdir)
    run_git(['checkout', 'master'], tempdir)
    run_git(['merge', '--no-ff', 'feature2', '-m', 'Merge feature2'], tempdir)
    merge_commit2 = run_git(['rev-parse', 'HEAD'], tempdir)
    run_git(['tag', 'build-2', merge_commit2], tempdir)
    # 3rd merge: build tag (should be success)
    run_git(['checkout', '-b', 'feature3'], tempdir)
    with open(tempdir / 'file3.txt', 'w') as f:
        f.write('feature3\n')
    run_git(['add', 'file3.txt'], tempdir)
    run_git(['commit', '-m', 'Feature 3'], tempdir)
    run_git(['checkout', 'master'], tempdir)
    run_git(['merge', '--no-ff', 'feature3', '-m', 'Merge feature3'], tempdir)
    merge_commit3 = run_git(['rev-parse', 'HEAD'], tempdir)
    run_git(['tag', 'build-3', merge_commit3], tempdir)
    print(run_git(['log','--graph'], tempdir))
    # Query merge commits
    merges = get_merge_commits(str(tempdir), '', '')
    prev_state = 'failed'
    states = []
    for m in merges:
        state = classify_tag_state(m['tags'], 'build-*', prev_state)
        states.append(state)
        prev_state = state if state != 'recovery' else 'success'
    assert states == ['failed', 'recovery', 'success']
