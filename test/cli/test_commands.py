import re

from typer.testing import CliRunner

from lauschkiste_cli.cli import ctl, server

runner = CliRunner()


def plain(output: str) -> str:
    """Help text without the colors rich adds on CI (GITHUB_ACTIONS forces a terminal)."""
    return re.sub(r'\x1b\[[0-9;]*m', '', output)


def test_server_runs_without_a_subcommand():
    result = runner.invoke(server, ['--help'])
    assert result.exit_code == 0
    assert 'Run the Lauschkiste server' in plain(result.output)
    assert '--home' in plain(result.output) and '--conf' in plain(result.output)


def test_lauschctl_has_the_management_commands_but_not_run():
    result = runner.invoke(ctl, ['--help'])
    assert result.exit_code == 0
    for command in ('home', 'setup', 'update', 'plugin', 'debug'):
        assert command in plain(result.output)
    assert runner.invoke(ctl, ['run', '--help']).exit_code != 0

