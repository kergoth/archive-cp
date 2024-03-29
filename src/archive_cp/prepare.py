"""Prepare our grouped paths into a form we can apply to the target directory."""
import collections
import datetime
from pathlib import Path
from typing import (
    Callable,
    Dict,
    Generator,
    List,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
    Tuple,
    TypeAlias,
)

from archive_cp.fileutils import sha256sum, zip_chksum
from archive_cp.group import base_name
from archive_cp.pathutils import is_relative_to, mtime

TimeFunc: TypeAlias = Callable[[Path], datetime.datetime]
DirectoryState: TypeAlias = Mapping[Path, Path]
PathSequence: TypeAlias = Sequence[Path]
FileOperation: TypeAlias = Tuple[Path, PathSequence, DirectoryState, PathSequence]


def prepare_file_operations(
    target_directory: Path,
    grouped: Mapping[Path, List[List[Path]]],
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
        file_times: Dict[Path, datetime.datetime] = {}

        def timefunc(f: Path) -> datetime.datetime:
            return file_times[f]

        for group in groups:
            for f in group:
                file_times[f] = mtime(f)

            if len(group) > 1:
                selected, group_unselected = deduplicate(group, destdir, timefunc)
                files.append(selected)
                unselected.extend(group_unselected)
            else:
                files.append(group[0])

        by_mtime = sorted(files, key=timefunc, reverse=True)
        newest = by_mtime[0]

        uniques, discarded = unique_names(by_mtime[1:], timefunc=timefunc)
        new_state = {base_name(newest.name, newest): newest}
        new_state.update(uniques)
        unselected.extend(discarded)

        yield destdir, old_state, new_state, unselected


def deduplicate(
    group: Sequence[Path], target_directory: Path, timefunc: TimeFunc
) -> Tuple[Path, List[Path]]:
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
    paths: Sequence[Path],
    timefunc: TimeFunc,
    ignore_case: bool = False,
) -> Tuple[Dict[Path, Path], Sequence[Path]]:
    """Ensure that the path filenames are as unique as possible."""
    uniques: Dict[Path, Path] = {}
    by_name: MutableMapping[Path, MutableSequence[Path]] = collections.defaultdict(list)
    discarded: MutableSequence[Path] = []

    # Group by the source file base name, not the normalized relpath,
    # thereby ensuring we don't force everything to lowercase.
    for path in paths:
        by_name[base_name(path.name, path)].append(path)

    increase_uniqueness(
        by_name, uniques, lambda p, n: add_chksum_stem_suffix(p, n, ignore_case)
    )

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
    by_name: MutableMapping[Path, MutableSequence[Path]],
    uniques: Dict[Path, Path],
    namefunc: Callable[[Path, Path], Path],
) -> None:
    """Increase uniqueness for non-unique filenames, tracking those remaining.

    This function mutates the by_name and uniques arguments.
    """
    for newname, paths in list(by_name.items()):

        def new_namefunc(path: Path, newname: Path = newname) -> Path:
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
    paths: Sequence[Path], namefunc: Callable[[Path], Path]
) -> Tuple[Mapping[Path, Path], Mapping[Path, MutableSequence[Path]]]:
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


def add_chksum_stem_suffix(
    path: Path, name: Path, ignore_case: bool = False, enable_zip: bool = False
) -> Path:
    """Add a checksum suffix to the path's stem."""
    extension = path.suffix.lower() if ignore_case else path.suffix
    if enable_zip and extension == ".zip":
        chksum, _ = zip_chksum(path)
        if not chksum:
            chksum = sha256sum(path)
    else:
        chksum = sha256sum(path)

    return Path(f"{name.stem}.{chksum[:8]}{name.suffix}")
