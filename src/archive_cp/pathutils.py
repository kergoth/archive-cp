import datetime
import os
import pathlib


def is_relative_to(path: os.PathLike[str], directory: os.PathLike[str]) -> bool:
    return str(path).startswith(str(directory) + "/")


def mtime(path: pathlib.Path) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(
        path.lstat().st_mtime, tz=datetime.timezone.utc
    )
