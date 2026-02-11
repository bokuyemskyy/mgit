import os
from argparse import _SubParsersAction

from app.cli import logger
from app.objects import GitBlob, GitCommit, GitTree
from app.repository import GitRepository
from app.repository.branch import is_branch_name, update_ref

from .command import cmd


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("checkout", help="Checkout a commit")
    parser.add_argument("commit", help="The commit to checkout")
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="The directory to checkout to (default: current directory)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force checkout, overwriting local changes",
    )
    parser.set_defaults(func=cmd_checkout)


@cmd(req_repo=True)
def cmd_checkout(args, repo: GitRepository) -> None:
    sha = repo.objects.find(args.commit)
    obj = repo.objects.read(sha)

    if not isinstance(obj, GitCommit):
        raise ValueError(f"object is not a commit: {sha}")

    tree_value = obj.kvlm.get_one(b"tree")
    if tree_value is None:
        raise ValueError("malformed commit")

    tree_obj = repo.objects.read(tree_value.decode("ascii"))

    if args.path is None:
        checkout_path = repo.worktree
    else:
        checkout_path = os.path.realpath(args.path)

        if os.path.exists(checkout_path):
            if not os.path.isdir(checkout_path):
                raise Exception(f"not a directory: {checkout_path}")
            if os.listdir(checkout_path):
                raise Exception(f"not empty: {checkout_path}")
        else:
            os.makedirs(checkout_path)

    if checkout_path == repo.worktree:
        if not args.force:
            conflicts = check_conflicts(repo, tree_obj, checkout_path)
            if conflicts:
                logger.info(
                    "error: Your changes to the following files would be overwritten by checkout:"
                )
                for conflict in conflicts:
                    logger.info(f"\t{conflict}")
                logger.info("Aborting.")
                raise Exception(
                    "Checkout aborted due to conflicts. Use --force to override."
                )

    tree_checkout(repo, tree_obj, checkout_path)

    if checkout_path == repo.worktree:
        is_branch_checkout = is_branch_name(repo, args.commit)

        update_ref(repo, sha, args.commit if is_branch_checkout else None)

        if not is_branch_checkout:
            logger.info(f"Note: switching to '{args.commit}'.\n")
            logger.info("You are in 'detached HEAD' state\n")
            message = obj.kvlm.get_one(b"message")
            first_line = message.decode("utf8").split("\n")[0] if message else ""
            logger.info(f"HEAD is now at {sha[:7]} {first_line}")


def check_conflicts(repo: GitRepository, tree, path):
    conflicts = []

    for item in tree.items:
        dest = os.path.join(path, item.path)

        if isinstance(repo.objects.read(item.sha), GitTree):
            if os.path.exists(dest) and os.path.isdir(dest):
                tree_obj = repo.objects.read(item.sha)
                conflicts.extend(check_conflicts(repo, tree_obj, dest))
        else:
            if os.path.exists(dest):
                with open(dest, "rb") as f:
                    existing_content = f.read()

                blob = repo.objects.read(item.sha)
                assert isinstance(blob, GitBlob)
                if existing_content != blob.data:
                    rel_path = os.path.relpath(dest, path)
                    conflicts.append(rel_path)

    return conflicts


def tree_checkout(repo: GitRepository, tree, path):
    for item in tree.items:
        obj = repo.objects.read(item.sha)
        dest = os.path.join(path, item.path)

        if isinstance(obj, GitTree):
            if not os.path.exists(dest):
                os.mkdir(dest)
            tree_checkout(repo, obj, dest)
        elif isinstance(obj, GitBlob):
            with open(dest, "wb") as obj_file:
                obj_file.write(obj.data)
