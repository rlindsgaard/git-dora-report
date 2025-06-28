import subprocess
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

def create_feature(tempdir, faker):
    branch_name = faker.word()
    file_name = faker.file_name(extension='txt')
    content = faker.text()
    commit_message = faker.sentence()
    run_git(['checkout', 'master'], tempdir)
    run_git(['checkout', '-b', branch_name], tempdir)
    with open(tempdir / file_name, 'w') as f:
        f.write(content)
    run_git(['add', file_name], tempdir)
    run_git(['commit', '-m', commit_message], tempdir)
    run_git(['checkout', 'master'], tempdir)
    run_git(['merge', '--no-ff', branch_name, '-m', f'Merge {branch_name}'], tempdir)

@pytest.fixture
def good_feature(faker):
    def _good_feature(tempdir, tag_name):
        create_feature(tempdir, faker)
        run_git(['tag', tag_name], tempdir)
    return _good_feature

@pytest.fixture
def bad_feature(faker):
    def _bad_feature(tempdir):
        create_feature(tempdir, faker)

    return _bad_feature

def test_pipeline_tag_classification_integration(tmp_path, good_feature, bad_feature):
    tempdir = tmp_path
    run_git(['init'], tempdir)
    run_git(['config', 'user.email', 'test@example.com'], tempdir)
    run_git(['config', 'user.name', 'Test User'], tempdir)
    with open(tempdir / 'file.txt', 'w') as f:
        f.write('init\n')
    run_git(['add', 'file.txt'], tempdir)
    run_git(['commit', '-m', 'Initial commit'], tempdir)

    # 1st merge: no tag (should be failed)
    bad_feature(tempdir)

    # 2nd merge: build tag (should be recovery)
    good_feature(tempdir, 'build-1')

    # 3rd merge: build tag (should be success)
    good_feature(tempdir, 'build-2')

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
