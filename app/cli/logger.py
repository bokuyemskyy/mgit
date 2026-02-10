import logging
import sys

logger = logging.getLogger("mgit")
logger.setLevel(logging.INFO)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.addFilter(lambda record: record.levelno < logging.WARNING)

stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.WARNING)

stdout_formatter = logging.Formatter("%(message)s")
stdout_handler.setFormatter(stdout_formatter)


stderr_formatter = logging.Formatter("fatal: %(message)s")
stderr_handler.setFormatter(stderr_formatter)

logger.addHandler(stdout_handler)
logger.addHandler(stderr_handler)
