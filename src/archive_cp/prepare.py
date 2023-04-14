import collections
import pathlib
from typing import List
from typing import Tuple

from archive_cp.fileutils import sha256sum
from archive_cp.group import base_name
from archive_cp.group import duplicate_groups
from archive_cp.pathutils import is_relative_to
from archive_cp.pathutils import mtime


def prepare_file_operations(target_directory, sources, ignore_case, quiet):
    grouped = duplicate_groups(sources, target_directory, ignore_case, quiet)
    for relpath, groups in grouped.items():
        destdir = target_directory / relpath.parent
        target_state = [
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

        basename = pathlib.Path(relpath.name)
        uniques, discarded = unique_names(by_mtime[1:], basename, timefunc=mtime)

        newest_base = pathlib.Path(base_name(newest.name) or newest.name)
        new_state = {newest_base: newest}
        new_state.update(uniques)
        unselected.extend(discarded)

        yield destdir, target_state, new_state, unselected


def deduplicate(
    group, target_directory, timefunc
) -> Tuple[pathlib.Path, List[pathlib.Path]]:
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


def unique_names(paths, basename, timefunc):
    uniques, by_name, discarded = {}, collections.defaultdict(list), []

    # Group by the source file base name, not the normalized relpath,
    # thereby ensuring we don't force everything to lowercase.
    for path in paths:
        name = pathlib.Path(base_name(path.name) or path.name)
        by_name[name].append(path)

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


def increase_uniqueness(by_name, uniques, namefunc):
    for newname, paths in list(by_name.items()):
        some_unique, new_by_name = unique_names_by(
            paths, lambda p: namefunc(p, newname)
        )
        if True or some_unique:
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


def unique_names_by(paths, namefunc):
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


def add_time_stem_suffix(path, name, timefunc, format="%Y%m%dT%H%M%S"):
    timestr = timefunc(path).strftime(format)
    return pathlib.Path(f"{name.stem}.{timestr}{name.suffix}")


def add_chksum_stem_suffix(path, name):
    chksum = sha256sum(path)
    return pathlib.Path(f"{name.stem}.{chksum[:8]}{name.suffix}")
