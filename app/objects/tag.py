from .commit import GitCommit


class GitTag(GitCommit):
    format = b"tag"
