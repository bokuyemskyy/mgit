import functools
from app.cli import logger
from app.repository import GitRepository


def command(requires_repo=False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(args):
            try:
                repo = GitRepository.find() if requires_repo else None
                return func(args, repo) if requires_repo else func(args)
            except Exception as e:
                logger.error(f"Error: {e}")

        return wrapper

    return decorator
