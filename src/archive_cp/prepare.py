"""Prepare our grouped paths into a form we can apply to the target directory."""
import collections
import datetime
import pathlib
from typing import Callable
from typing import Dict
from typing import Generator
from typing import List
from typing import Mapping
from typing import MutableMapping
from typing import MutableSequence
from typing import Sequence
from typing import Tuple
from typing import TypeAlias

from archive_cp.fileutils import sha256sum
from archive_cp.group import base_name
from archive_cp.pathutils import is_relative_to
from archive_cp.pathutils import mtime


TimeFunc: TypeAlias = Callable[[pathlib.Path], datetime.datetime]
DirectoryState: TypeAlias = Mapping[pathlib.Path, pathlib.Path]
PathSequence: TypeAlias = Sequence[pathlib.Path]
FileOperation: TypeAlias = Tuple[
    pathlib.Path, PathSequence, DirectoryState, PathSequence
]


def prepare_file_operations(
    target_directory: pathlib.Path,
    grouped: Mapping[pathlib.Path, List[List[pathlib.Path]]],
) -> Generator[FileOperation, None, None]:
    """Gather files, preparing the file operations to be performed given our rules."""
    for relpath, groups in grouped.items():
        destdir = target_directory / relpath.parent
        old_state = [
            p.relative_to(destdir)
            for g in groups
            for p in g
            if is_relative_to(p, destdir)
        ]
        unselected = []

        files = []
        for group in groups:
            if len(group) > 1:
                selected, group_unselected = deduplicate(group, destdir, timefunc=mtime)
                files.append(selected)
                unselected.extend(group_unselected)
            else:
                files.append(group[0])

        by_mtime = list(sorted(files, key=lambda f: mtime(f), reverse=True))
        newest = by_mtime[0]

        uniques, discarded = unique_names(by_mtime[1:], timefunc=mtime)
        new_state = {base_name(newest.name): newest}
        new_state.update(uniques)
        unselected.extend(discarded)

        yield destdir, old_state, new_state, unselected


def deduplicate(
    group: Sequence[pathlib.Path], target_directory: pathlib.Path, timefunc: TimeFunc
) -> Tuple[pathlib.Path, List[pathlib.Path]]:
    """Sort a group of files, selecting the oldest to keep in a consistent way."""
    # Sort by path
    group = sorted(group)
    # Sort files already in the target directory to the beginning
    group = sorted(
        group,
        key=lambda s: is_relative_to(s, target_directory),
        reverse=True,
    )
    # Sort by modification date, keeping the oldest
    group = sorted(group, key=timefunc)
    return group[0], group[1:]


def unique_names(
    paths: Sequence[pathlib.Path], timefunc: TimeFunc
) -> Tuple[Dict[pathlib.Path, pathlib.Path], Sequence[pathlib.Path]]:
    """Ensure that the path filenames are as unique as possible."""
    uniques: Dict[pathlib.Path, pathlib.Path] = {}
    by_name: MutableMapping[
        pathlib.Path, MutableSequence[pathlib.Path]
    ] = collections.defaultdict(list)
    discarded: MutableSequence[pathlib.Path] = []

    # Group by the source file base name, not the normalized relpath,
    # thereby ensuring we don't force everything to lowercase.
    for path in paths:
        by_name[base_name(path.name)].append(path)

    increase_uniqueness(
        by_name, uniques, lambda p, n: add_time_stem_suffix(p, n, timefunc)
    )
    increase_uniqueness(by_name, uniques, add_chksum_stem_suffix)

    # Check for remaining non-unique paths with the same mtime and chksum
    for newname, paths in by_name.items():
        keep = paths[0]
        if newname not in uniques:
            uniques[newname] = keep
        else:
            raise Exception("wtf")

        discarded.extend(paths[1:])

    return uniques, discarded


def increase_uniqueness(
    by_name: MutableMapping[pathlib.Path, MutableSequence[pathlib.Path]],
    uniques: Dict[pathlib.Path, pathlib.Path],
    namefunc: Callable[[pathlib.Path, pathlib.Path], pathlib.Path],
) -> None:
    """Increase uniqueness for non-unique filenames, tracking those remaining.

    This function mutates the by_name and uniques arguments.
    """
    for newname, paths in list(by_name.items()):

        def new_namefunc(
            path: pathlib.Path, newname: pathlib.Path = newname
        ) -> pathlib.Path:
            return namefunc(path, newname)

        some_unique, new_by_name = unique_names_by(paths, new_namefunc)
        uniques.update(some_unique)
        by_name[newname] = []
        for _newname, _paths in new_by_name.items():
            if _newname in by_name:
                by_name[_newname].extend(_paths)
            else:
                by_name[_newname] = _paths

    for newname in list(by_name):
        paths = by_name[newname]
        if not paths:
            del by_name[newname]


def unique_names_by(
    paths: Sequence[pathlib.Path], namefunc: Callable[[pathlib.Path], pathlib.Path]
) -> Tuple[
    Mapping[pathlib.Path, pathlib.Path],
    Mapping[pathlib.Path, MutableSequence[pathlib.Path]],
]:
    """Determine unique and non-unique paths after adjusting the filenames."""
    by_newname = collections.defaultdict(list)
    for path in paths:
        newname = namefunc(path)
        by_newname[newname].append(path)

    unique, remaining = {}, {}
    for newname, newpaths in by_newname.items():
        if len(newpaths) == 1:
            unique[newname] = newpaths[0]
        else:
            remaining[newname] = newpaths

    return unique, remaining


def add_time_stem_suffix(
    path: pathlib.Path,
    name: pathlib.Path,
    timefunc: TimeFunc,
    format: str = "%Y%m%dT%H%M%S",
) -> pathlib.Path:
    """Add a timestamp suffix to the path's stem."""
    timestr = timefunc(path).strftime(format)
    return pathlib.Path(f"{name.stem}.{timestr}{name.suffix}")


def add_chksum_stem_suffix(path: pathlib.Path, name: pathlib.Path) -> pathlib.Path:
    """Add a checksum suffix to the path's stem."""
    chksum = sha256sum(path)
    return pathlib.Path(f"{name.stem}.{chksum[:8]}{name.suffix}")
