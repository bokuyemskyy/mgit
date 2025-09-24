from app.repository import repository_find, object_read, GitCommit


def setup_parser(subparsers):
    parser = subparsers.add_parser(
        "log",
        help="Show history of a commit",
    )
    parser.add_argument("commit", default="HEAD", nargs="?", help="Starting commit")
    parser.set_defaults(func=command_log)


def command_log(args):
    repo = repository_find()

    seen = set()

    for sha in iterate_commits(repo, args.commit, seen):
        commit = object_read(repo, sha)
        if not isinstance(commit, GitCommit):
            raise ValueError(f"Object {sha} is not a commit")
        print_commit(commit, sha)


def iterate_commits(repository, sha, seen):
    if sha in seen:
        return

    seen.add(sha)
    commit = object_read(repository, sha)

    if not isinstance(commit, GitCommit):
        raise ValueError(f"Object {sha} is not a commit")

    parents = commit.kvlm.get(b"parent", [])

    if not isinstance(parents, list):
        parents = [parents]

    for parent in parents:
        yield from iterate_commits(repository, parent, seen)

    yield sha


def print_commit(commit: GitCommit, sha):
    kvlm = commit.kvlm

    print(f"commit {sha.decode("ascii")}")
    if b"author" in kvlm:
        for author in kvlm[b"author"]:
            print(f"Author: {author.decode('utf-8')}")

    if b"date" in kvlm:
        for date in kvlm[b"date"]:
            print(f"Date:   {date.decode('utf-8')}")

    message = kvlm.get(None, [b""])[0].decode("utf-8")

    print()
    for line in message.splitlines():
        print(f"    {line}")
    print()
