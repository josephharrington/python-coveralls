from collections import namedtuple
import os

try:
    from subprocess32 import check_output
except ImportError:
    from subprocess import check_output

FORMAT = '%n'.join(['%H', '%aN', '%ae', '%cN', '%ce', '%s'])
CommitInfo = namedtuple(
    'CommitInfo', ['hash', 'author_name', 'author_email', 'committer_name', 'committer_email', 'subject'])


def _git_commit_info():
    """Return a CommitInfo object describing the current head commit."""
    raw_info = check_output(
        ['git', '--no-pager', 'log', '-1', '--pretty=format:%s' % FORMAT],
        universal_newlines=True
    ).split('\n', 5)
    return CommitInfo(hash=raw_info[0], author_name=raw_info[1], author_email=raw_info[2], committer_name=raw_info[3],
                      committer_email=raw_info[4], subject=raw_info[5].strip())


def _git_current_branch():
    """Return the name of the current git branch."""
    return check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], universal_newlines=True).strip()


def _git_fetch_remotes():
    """Return the list of git fetch remotes in the form: tuple(remote_name, remote_url)."""
    all_remotes = check_output(['git', 'remote', '-v'], universal_newlines=True).strip().splitlines()
    return [s.split() for s in all_remotes if s.endswith('(fetch)')]


def gitrepo(root):
    tmpdir = os.getcwd()
    os.chdir(root)
    commit_info = _git_commit_info()
    branch = (os.environ.get('CIRCLE_BRANCH') or
              os.environ.get('TRAVIS_BRANCH', _git_current_branch()))
    remotes = _git_fetch_remotes()
    os.chdir(tmpdir)
    return {
        "head": {
            "id": commit_info.hash,
            "author_name": commit_info.author_name,
            "author_email": commit_info.author_email,
            "committer_name": commit_info.committer_name,
            "committer_email": commit_info.committer_email,
            "message": commit_info.subject,
        },
        "branch": branch,
        "remotes": [{'name': remote[0], 'url': remote[1]} for remote in remotes]
    }


HGLOG = """{node}
{author|person}
{author|email}
{author|person}
{author|email}
{desc}"""


def hgrepo(root):
    hglog = sh.hg('log', '-l', '1', template=HGLOG).split('\n', 5)
    branch = (os.environ.get('CIRCLE_BRANCH') or
              os.environ.get('TRAVIS_BRANCH', sh.hg('branch').strip()))
    remotes = [x.split(' = ') for x in sh.hg('paths')]
    return {
        'head': {
            'id': hglog[0],
            'author_name': hglog[1],
            'author_email': hglog[2],
            'committer_name': hglog[3],
            'committer_email': hglog[4],
            'message': hglog[5].strip(),
        },
        'branch': branch,
        'remotes': [{
            'name': remote[0], 'url': remote[1]
        } for remote in remotes]
    }


def repo(root):
    if '.git' in os.listdir(root):
        return gitrepo(root)
    if '.hg' in os.listdir(root):
        return hgrepo(root)
