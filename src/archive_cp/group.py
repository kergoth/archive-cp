"""Group files by duplicates with matching relative filenames, using fclones."""

import collections
import os
import pathlib
import re
import subprocess
from typing import List
from typing import Mapping

from archive_cp.pathutils import is_relative_to


DEVNULL = os.open(os.devnull, os.O_WRONLY)
ADJUSTED_FN_TIME = re.compile(r"^(.*)\.[0-9]{8}T[0-9]{6}(\.[^.]+)?$")
ADJUSTED_FN_TIME_CHKSUM = re.compile(
    r"^(.*)\.[0-9]{8}T[0-9]{6}\.[0-9a-zA-Z]{8}(\.[^.]+)?$"
)


def duplicate_groups(
    sources: Mapping[pathlib.Path, pathlib.Path],
    target: pathlib.Path,
    ignore_case=False,
    quiet=False,
) -> Mapping[pathlib.Path, List[pathlib.Path]]:
    by_dest = collections.defaultdict(list)
    paths = sources.keys()
    grouped = fclones(paths, suppress_err=quiet)
    for group in grouped:
        # Regroup within a set of duplicates, by relative destination path
        regrouped = collections.defaultdict(list)
        for item in group:
            if is_relative_to(item, target):
                dest = item.relative_to(target)
                adjusted = base_name(dest)
                if adjusted:
                    dest = pathlib.Path(adjusted)
            else:
                dest = file_destination(item, sources).relative_to(target)

            if ignore_case:
                normalized = pathlib.Path(str(dest).lower())
                regrouped[normalized].append(item)
            else:
                regrouped[dest].append(item)

        # Collect groups of duplicates by dest
        for dest, items in regrouped.items():
            by_dest[dest].append(items)

    return by_dest


def fclones(files: List[pathlib.Path], suppress_err=False, args=None):
    if args is None:
        args = ["-H", "-f", "fdupes", "--rf-over=0", "--min=0"]

    stderr = DEVNULL if suppress_err else None
    output = subprocess.check_output(
        ["fclones", "group"] + args + [str(f) for f in files],
        stderr=stderr,
    )
    return fclones_grouped(output.decode("utf-8"))


def fclones_grouped(output):
    block = []
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


def base_name(name):
    """Return the base name, undoing the timestamp suffixes resulting from this script."""
    for pattern in [ADJUSTED_FN_TIME_CHKSUM, ADJUSTED_FN_TIME]:
        m = pattern.match(str(name))
        if m:
            if m.group(2):
                return m.group(1) + m.group(2)
            else:
                return m.group(1)


def file_destination(filepath, sources):
    if filepath in sources:
        return sources[filepath]
    else:
        for source_file in sources:
            if source_file.is_dir() and is_relative_to(filepath, source_file):
                return sources[source_file] / filepath.relative_to(source_file)
    raise NotImplementedError()
