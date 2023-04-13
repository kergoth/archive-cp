import datetime
import pathlib
from typing import Union


def is_relative_to(
    path: Union[str, pathlib.Path], directory: Union[str, pathlib.Path]
) -> bool:
    return str(path).startswith(str(directory) + "/")


def mtime(path: pathlib.Path, tz=datetime.timezone.utc) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(path.lstat().st_mtime, tz=tz)
