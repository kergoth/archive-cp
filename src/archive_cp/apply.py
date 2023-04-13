import os
import pathlib
import tempfile
from typing import Mapping
from typing import Sequence

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
    log,
) -> None:
    in_target, external = [], []
    for newname, path in new_state.items():
        if is_relative_to(path, target_directory):
            in_target.append((newname, path))
        else:
            external.append((newname, path))

    if not dry_run:
        target_directory.mkdir(parents=True, exist_ok=True)
        tempdir = tempfile.TemporaryDirectory(dir=target_directory)

    try:
        postponed = []

        for newname, path in in_target:
            relpath = path.relative_to(target_directory)
            if newname == relpath:
                if debug:
                    log(f"skipped {path} (nothing to do)")
            else:
                dest = target_directory / newname
                if not dry_run:
                    if newname in old_state:
                        tmpfile = pathlib.Path(tempdir.name) / newname.name
                        link_file(path, tmpfile)
                        postponed.append((path, tmpfile, dest))
                    else:
                        os.rename(path, dest)

                        if verbose or dry_run:
                            log(f"renamed '{path}' -> '{dest}'")

        for path, tmpfile, dest in postponed:
            os.rename(tmpfile, dest)
            path.unlink()
            if verbose or dry_run:
                log(f"renamed '{path}' -> '{dest}'")
    finally:
        if not dry_run:
            tempdir.cleanup()

    for newname, path in external:
        dest = target_directory / newname
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.unlink(missing_ok=True)
            copy_file(path, dest)

        if verbose or dry_run:
            log(f"'{path}' -> '{dest}'")

    to_remove = (
        set(old_state)
        - set(new_state.keys())
        - set(v.relative_to(target_directory) for k, v in in_target)
    )
    for path in to_remove:
        if path.exists():
            if not dry_run:
                path.unlink()

            if verbose or dry_run:
                log(f"removed '{path}'")
