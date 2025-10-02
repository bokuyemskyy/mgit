from __future__ import annotations
from argparse import _SubParsersAction

from .command import cmd
from app.repository import GitRepository
from app.objects import GitTag

from .show_ref import show_ref


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("tag", help="List and create tags")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list", "-l", action="store_true", help="List all tags")
    group.add_argument(
        "-a", action="store_true", dest="create_tag", help="Create an annotated tag"
    )

    parser.add_argument("name", nargs="?", help="Tag name")
    parser.add_argument(
        "object", default="HEAD", nargs="?", help="Object the tag points to"
    )

    parser.set_defaults(func=cmd_tag)


@cmd(req_repo=True)
def cmd_tag(args, repo) -> None:
    if args.list:
        tags = repo.ref_list()["tags"]
        if isinstance(tags, dict):
            show_ref(tags, with_hash=False)
    elif args.create_tag:
        tag_create(
            repo, args.name, args.object, create_tag_object=args.create_tag_object
        )
    else:
        tags = repo.ref_list()["tags"]
        if isinstance(tags, dict):
            show_ref(tags, with_hash=False)


def tag_create(repo: GitRepository, name, ref, create_tag_object=False):
    sha = repo.objects.object_find(ref)

    if create_tag_object:
        tag = GitTag()
        tag.kvlm[b"object"] = [sha.encode()]
        tag.kvlm[b"type"] = [b"commit"]
        tag.kvlm[b"tag"] = [name.encode()]
        # tag.kvlm[b"tagger"]
        # tag.kvlm[None]

        tag_sha = repo.objects.object_write(tag)
        repo.refs.ref_create("tags", name, sha=tag_sha)
    else:
        repo.refs.ref_create("tags", name, sha=sha)
