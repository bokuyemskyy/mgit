from typing import Optional

from .repository import GitRepository


def get_current_branch(repo: GitRepository):
    content = repo.fs.file_read("HEAD", binary=False)
    if content.startswith("ref: refs/heads/"):
        return content[16:].strip()
    else:
        return None


def update_ref(repo: GitRepository, commit_sha: str, branch_name: Optional[str] = None):
    if branch_name:
        ref_path = f"refs/heads/{branch_name}"
        repo.fs.file_write(ref_path, content=f"{commit_sha}\n")

        repo.fs.file_write("HEAD", content=f"ref: refs/heads/{branch_name}\n")
    else:
        current_branch = get_current_branch(repo)

        if current_branch:
            # Update current branch
            ref_path = f"refs/heads/{current_branch}"
            repo.fs.file_write(ref_path, content=f"{commit_sha}\n")
        else:
            # Detached HEAD state
            repo.fs.file_write("HEAD", content=f"{commit_sha}\n")


def is_branch_name(repo: GitRepository, name: str) -> bool:
    try:
        ref_path = f"refs/heads/{name}"
        if repo.fs.file_exists(ref_path):
            return True

        current_branch = get_current_branch(repo)
        if current_branch and current_branch == name:
            return True

        return False
    except Exception:
        return False
