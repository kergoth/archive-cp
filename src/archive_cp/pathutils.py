import datetime
import os
import pathlib


def is_relative_to(path: os.PathLike[str], directory: os.PathLike[str]) -> bool:
    """Determine whether path is relative to directory."""
    return str(path).startswith(str(directory) + "/")


def mtime(path: pathlib.Path) -> datetime.datetime:
    """Return the modification time of a path as a datetime object, assuming a timezone of utc."""
    return datetime.datetime.fromtimestamp(
        path.lstat().st_mtime, tz=datetime.timezone.utc
    )
