"""Functions for operating on file paths."""
import datetime
import os
from pathlib import Path


def is_relative_to(path: os.PathLike[str], directory: os.PathLike[str]) -> bool:
    """Determine whether path is relative to directory."""
    return str(Path(path).resolve()).startswith(str(Path(directory).resolve()) + "/")


def mtime(path: Path) -> datetime.datetime:
    """Return the modification time of a path as a datetime object.

    Assumes a timezone of utc, not the current timezone.
    """
    return datetime.datetime.fromtimestamp(
        path.lstat().st_mtime, tz=datetime.timezone.utc
    )
