# Archive Cp

[![PyPI](https://img.shields.io/pypi/v/archive-cp.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/archive-cp.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/archive-cp)][pypi status]
[![License](https://img.shields.io/pypi/l/archive-cp)][license]

[![The Ethical Source Principles](https://img.shields.io/badge/ethical-source-%23bb8c3c?labelColor=393162)][ethical source]
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.0-4baaaa.svg)][codeofconduct]
[![Read the documentation at https://archive-cp.readthedocs.io/](https://img.shields.io/readthedocs/archive-cp/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/kergoth/archive-cp/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/kergoth/archive-cp/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

archive-cp is a small utility intended to be used to copy files with the goal of
not losing data, for archival purposes. If files would be the same name in the
target directory, and they aren't duplicates, all of them are kept. Duplicates
are identified, the oldest of each group of duplicates sharing a name and
destdir is selected, of the remaining items, the newest gets the original
filename, the others are timestamped to give them unique names.

The `fclones` tool is required for duplicate file detection.

As the author, my original use of this project was to combine multiple mirrors
of old ftp sites without losing old versions of old tools, since it's not always
easy to identify which mirror is the most recent, which are complete or
incomplete, and even if they're all complete, files got replaced or removed over
time, so there's value in being able to merge them.

## Features

- TODO

## Requirements

- TODO

## Installation

You can install _Archive Cp_ via [pip] from [PyPI]:

```console
$ pip install archive-cp
```

## Usage

Please see the [Command-line Reference] for details.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_Archive Cp_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [@cjolowicz]'s [Hypermodern Python Cookiecutter] template.

[pypi status]: https://pypi.org/project/archive-cp/
[ethical source]: https://ethicalsource.dev/principles/
[read the docs]: https://archive-cp.readthedocs.io/
[tests]: https://github.com/kergoth/archive-cp/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/kergoth/archive-cp
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

[@cjolowicz]: https://github.com/cjolowicz
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/cjolowicz/cookiecutter-hypermodern-python
[file an issue]: https://github.com/kergoth/archive-cp/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/kergoth/archive-cp/blob/main/LICENSE
[contributor guide]: https://github.com/kergoth/archive-cp/blob/main/CONTRIBUTING.md
[command-line reference]: https://archive-cp.readthedocs.io/en/latest/usage.html
[codeofconduct]: https://github.com/kergoth/archive-cp/blob/main/CODE_OF_CONDUCT.md
