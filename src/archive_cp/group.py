"""Group files by duplicates with matching relative filenames, using fclones."""

import collections
import os
import re
import subprocess
from pathlib import Path
from typing import Callable, Generator, Iterable, List, Mapping, Optional, Sequence

from archive_cp.fileutils import StrPath, sha256sum
from archive_cp.pathutils import is_relative_to

DEVNULL = os.open(os.devnull, os.O_WRONLY)
ADJUSTED_FN_CHKSUM = re.compile(r"^(.*)\.([0-9a-zA-Z]{8})(\.[^.]+)?$")


def duplicate_groups(
    target_directory: Path,
    dupes: Iterable[Iterable[Path]],
    file_destination: Callable[[Path], Path],
    ignore_case: bool = False,
) -> Mapping[Path, List[List[Path]]]:
    """Run fclones on the source paths, grouping by relative destination path."""
    by_relpath = collections.defaultdict(list)
    for group in dupes:
        # Regroup within a set of duplicates, by relative destination path
        regrouped = collections.defaultdict(list)
        for item in group:
            if is_relative_to(item, target_directory):
                relpath = base_name(item.relative_to(target_directory), item)
            else:
                relpath = file_destination(item)

            if ignore_case:
                normalized = Path(str(relpath).lower())
                regrouped[normalized].append(item)
            else:
                regrouped[relpath].append(item)

        # Collect groups of duplicates by relpath
        for relpath, items in regrouped.items():
            by_relpath[relpath].append(items)

    return by_relpath


def fclones(
    files: Iterable[Path],
    suppress_err: bool = False,
    extra_args: Optional[List[str]] = None,
) -> Generator[Sequence[Path], None, None]:
    """Run fclones on the specified files, returning a list of groups of file paths."""
    stderr = DEVNULL if suppress_err else None
    cmd = [
        "fclones",
        "group",
        "-f",
        "fdupes",
        "--stdin",
        "-H",
        "--rf-over=0",
    ]
    if extra_args:
        cmd += extra_args

    output = subprocess.check_output(
        cmd,
        stderr=stderr,
        input="".join(str(f) + "\n" for f in files).encode("utf-8"),
    )
    return fclones_grouped(output.decode("utf-8"))


def fclones_grouped(output: str) -> Generator[Sequence[Path], None, None]:
    """Parse the output of fclones into a list of groups of file paths.

    Command output is assumed to be in 'fdupes' format.
    """
    block: List[Path] = []
    for line in output.splitlines():
        line = line.rstrip("\r\n")
        if not line:
            if block:
                yield block
            block.clear()
        else:
            block.append(Path(line))

    if block:
        yield block


def base_name(name: StrPath, path: StrPath) -> Path:
    """Return the base name, undoing the suffixes resulting from this script."""
    m = ADJUSTED_FN_CHKSUM.match(str(name))
    if m:
        prefix, chksum, suffix = m.group(1), m.group(2), m.group(3)
        if chksum and sha256sum(path)[:8] == chksum:
            name = prefix + (suffix or "")
    return Path(name)


def file_destination(filepath: Path, sources: Mapping[Path, Path]) -> Path:
    """Determine the appropriate destination for a given filepath, obeying sources."""
    if filepath in sources:
        return sources[filepath]
    else:
        for source_file in sources:
            if source_file.is_dir() and is_relative_to(filepath, source_file):
                return sources[source_file] / filepath.relative_to(source_file)
    raise NotImplementedError()
