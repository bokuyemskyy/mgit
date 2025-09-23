from app.repository import repository_find


def setup_parser(subparsers):
    parser = subparsers.add_parser(
        "log",
        help="Show history of a commit",
    )
    parser.add_argument("commit", default="HEAD", nargs="?", help="Starting commit")
    parser.set_defaults(func=command_log)


def command_log(args):
    repository = repository_find()

    seen = set()

    for sha in iterate_commits(repository, args.commit, seen):
        commit = object_read(repository, sha)
        print_commit(commit, sha)
