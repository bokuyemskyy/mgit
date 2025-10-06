import functools
from app.cli import logger
from app.repository import GitRepository


def cmd(req_repo=False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(args):
            try:
                repo = GitRepository.load() if req_repo else None
                return func(args, repo) if req_repo else func(args)
            except Exception as e:
                logger.error(f"{e}")

        return wrapper

    return decorator
