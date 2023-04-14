"""Test cases for the __main__ module."""
import pytest
from click.testing import CliRunner

from archive_cp import __main__


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


def test_main_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of two when no arguments are passed."""
    result = runner.invoke(__main__.main)
    assert result.exit_code == 2
