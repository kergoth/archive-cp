"""Command-line interface."""
import pathlib
from enum import Enum
from typing import Sequence
from typing import TextIO

import click

from archive_cp.apply import transition_state
from archive_cp.prepare import prepare_file_operations


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


class Verbosity(Enum):
    Quiet = -1
    Normal = 0
    Verbose = 1
    Debug = 2


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument(
    "source_files", nargs=-1, metavar="[SOURCE_FILE]...", type=click.Path(exists=True)
)
@click.option(
    "--file",
    "-f",
    help="Read SOURCE_FILE paths from the specified FILE."
    "'-' may be specified for standard input.",
    type=click.File(),
)
@click.argument("target_directory", nargs=1, type=click.Path(path_type=pathlib.Path))
@click.option(
    "--debug",
    "-d",
    "verbosity",
    is_flag=True,
    flag_value=Verbosity.Debug,
    help="Cause cp to be more verbose, showing files as they are processed.",
    type=Verbosity,
)
@click.option(
    "--verbose",
    "-v",
    "verbosity",
    is_flag=True,
    flag_value=Verbosity.Verbose,
    help="Cause cp to be verbose, showing files as they are copied.",
    type=Verbosity,
)
@click.option(
    "--quiet",
    "-q",
    "verbosity",
    is_flag=True,
    flag_value=Verbosity.Quiet,
    help="Cause cp to be quietier, showing fewer messages.",
    type=Verbosity,
)
@click.option(
    "--dry-run", "-n", is_flag=True, help="Dry run. Cause cp to pretend to copy files."
)
@click.option(
    "--ignore-case", "-i", is_flag=True, help="Ignore case in grouping files."
)
@click.version_option(package_name="archive_cp")
def main(
    source_files: Sequence[str],
    target_directory: pathlib.Path,
    file: TextIO,
    verbosity: Verbosity,
    dry_run: bool,
    ignore_case: bool,
) -> None:
    debug = verbosity == Verbosity.Debug
    verbose = verbosity in [Verbosity.Verbose, Verbosity.Debug]
    quiet = verbosity == Verbosity.Quiet

    target_directory = target_directory.resolve()
    if file:
        source_files = list(source_files) + [line.rstrip("\n") for line in file]

    sources = {}
    for orig_source in source_files:
        source = pathlib.Path(orig_source).resolve()
        if source.is_dir() and orig_source.endswith("/."):
            sources[source] = target_directory
        else:
            sources[source] = target_directory / source.name

    if target_directory.exists():
        sources[target_directory] = target_directory

    for destdir, old_state, new_state, unselected in prepare_file_operations(
        target_directory,
        sources,
        ignore_case,
        quiet,
    ):
        if debug:
            for path in unselected:
                click.echo(f"skipped {path} (unselected duplicate)")

        transition_state(
            destdir, old_state, new_state, verbose, debug, dry_run, log=click.echo
        )


if __name__ == "__main__":
    main(prog_name="archive-cp")  # pragma: no cover
