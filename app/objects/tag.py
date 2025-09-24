from .commit import GitCommit


class GitTag(GitCommit):
    fmt = b"tag"
