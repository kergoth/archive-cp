import os
import pathlib
import tempfile
from typing import Callable
from typing import Mapping
from typing import Sequence
from typing import Tuple

from archive_cp.fileutils import copy_file
from archive_cp.fileutils import link_file
from archive_cp.pathutils import is_relative_to


def transition_state(
    target_directory: pathlib.Path,
    old_state: Sequence[pathlib.Path],
    new_state: Mapping[pathlib.Path, pathlib.Path],
    verbose: bool,
    debug: bool,
    dry_run: bool,
    log: Callable[[str], None],
) -> None:
    """Apply the change in state from old to new to the target diretory."""
    in_target, postponed, external = [], [], []
    for newname, path in new_state.items():
        dest = target_directory / newname
        if is_relative_to(path, target_directory):
            relpath = path.relative_to(target_directory)
            if newname == relpath:
                if debug:
                    log(f"skipped {path} (nothing to do)")
            elif newname in old_state:
                postponed.append((dest, path))
                if debug:
                    log(f"postponed '{path}' ({dest} already present)")
            else:
                in_target.append((dest, path))
        else:
            external.append((dest, path))

    for dest, path in in_target:
        if not dry_run:
            os.rename(path, dest)

        if verbose or dry_run:
            log(f"renamed '{path}' -> '{dest}'")

    if not dry_run:
        rename_postponed(postponed, target_directory)

    if dry_run or verbose:
        for dest, path in postponed:
            log(f"renamed '{path}' -> '{dest}'")

    for dest, path in external:
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.unlink(missing_ok=True)
            copy_file(path, dest)

        if verbose or dry_run:
            log(f"'{path}' -> '{dest}'")

    to_remove = set(old_state) - set(new_state.keys()) - {v for k, v in in_target}
    for path in to_remove:
        if path.exists():
            if not dry_run:
                path.unlink()

            if verbose or dry_run:
                log(f"removed '{path}'")


def rename_postponed(
    postponed: Sequence[Tuple[pathlib.Path, pathlib.Path]],
    target_directory: pathlib.Path,
) -> None:
    """Rename target paths appropriately without conflict.

    A temporary directory is used to avoid conflicts.
    """
    target_directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target_directory) as tempdir:
        postponed_temp = []
        for dest, path in postponed:
            tmpfile = pathlib.Path(tempdir) / dest.name
            link_file(path, tmpfile)
            postponed_temp.append((tmpfile, dest))

        for tmpfile, dest in postponed_temp:
            dest.unlink(missing_ok=True)
            os.rename(tmpfile, dest)
