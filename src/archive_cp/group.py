"""Group files by duplicates with matching relative filenames, using fclones."""

import collections
import os
import pathlib
import re
import subprocess
from typing import Callable
from typing import Generator
from typing import Iterable
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence

from archive_cp.fileutils import StrPath
from archive_cp.pathutils import is_relative_to


DEVNULL = os.open(os.devnull, os.O_WRONLY)
ADJUSTED_FN_TIME = re.compile(r"^(.*)\.[0-9]{8}T[0-9]{6}(\.[^.]+)?$")
ADJUSTED_FN_TIME_CHKSUM = re.compile(
    r"^(.*)\.[0-9]{8}T[0-9]{6}\.[0-9a-zA-Z]{8}(\.[^.]+)?$"
)


def duplicate_groups(
    target_directory: pathlib.Path,
    dupes: Iterable[Iterable[pathlib.Path]],
    file_destination: Callable[[pathlib.Path], pathlib.Path],
    ignore_case: bool = False,
) -> Mapping[pathlib.Path, List[List[pathlib.Path]]]:
    """Run fclones on the source paths, grouping by relative destination path."""
    by_relpath = collections.defaultdict(list)
    for group in dupes:
        # Regroup within a set of duplicates, by relative destination path
        regrouped = collections.defaultdict(list)
        for item in group:
            if is_relative_to(item, target_directory):
                relpath = base_name(item.relative_to(target_directory))
            else:
                relpath = file_destination(item).relative_to(target_directory)

            if ignore_case:
                normalized = pathlib.Path(str(relpath).lower())
                regrouped[normalized].append(item)
            else:
                regrouped[relpath].append(item)

        # Collect groups of duplicates by relpath
        for relpath, items in regrouped.items():
            by_relpath[relpath].append(items)

    return by_relpath


def fclones(
    files: Iterable[pathlib.Path],
    suppress_err: bool = False,
    args: Optional[List[str]] = None,
) -> Generator[Sequence[pathlib.Path], None, None]:
    """Run fclones on the specified files, returning a list of groups of file paths."""
    if args is None:
        args = ["-H", "--rf-over=0", "--min=0"]

    stderr = DEVNULL if suppress_err else None
    output = subprocess.check_output(
        ["fclones", "group", "-f", "fdupes", "--stdin"] + args,
        stderr=stderr,
        input="".join(str(f) + "\n" for f in files).encode("utf-8"),
    )
    return fclones_grouped(output.decode("utf-8"))


def fclones_grouped(output: str) -> Generator[Sequence[pathlib.Path], None, None]:
    """Parse the output of fclones into a list of groups of file paths.

    Command output is assumed to be in 'fdupes' format.
    """
    block: List[pathlib.Path] = []
    for line in output.splitlines():
        line = line.rstrip("\r\n")
        if not line:
            if block:
                yield block
            block.clear()
        else:
            block.append(pathlib.Path(line))

    if block:
        yield block


def base_name(name: StrPath) -> pathlib.Path:
    """Return the base name, undoing the suffixes resulting from this script."""
    for pattern in [ADJUSTED_FN_TIME_CHKSUM, ADJUSTED_FN_TIME]:
        m = pattern.match(str(name))
        if m:
            if m.group(2):
                name = m.group(1) + m.group(2)
            else:
                name = m.group(1)
    return pathlib.Path(name)


def file_destination(
    filepath: pathlib.Path, sources: Mapping[pathlib.Path, pathlib.Path]
) -> pathlib.Path:
    """Determine the appropriate destination for a given filepath, obeying sources."""
    if filepath in sources:
        return sources[filepath]
    else:
        for source_file in sources:
            if source_file.is_dir() and is_relative_to(filepath, source_file):
                return sources[source_file] / filepath.relative_to(source_file)
    raise NotImplementedError()
