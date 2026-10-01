from typer.testing import CliRunner

from lauschkiste_cli.cli import ctl, legacy, server

runner = CliRunner()


def test_server_runs_without_a_subcommand():
    result = runner.invoke(server, ['--help'])
    assert result.exit_code == 0
    assert 'Run the Lauschkiste server' in result.output
    assert '--home' in result.output and '--conf' in result.output


def test_lauschctl_has_the_management_commands_but_not_run():
    result = runner.invoke(ctl, ['--help'])
    assert result.exit_code == 0
    for command in ('home', 'setup', 'update', 'plugin', 'debug'):
        assert command in result.output
    assert runner.invoke(ctl, ['run', '--help']).exit_code != 0


def test_old_jukebox_command_still_offers_run_and_setup():
    assert runner.invoke(legacy, ['run', '--help']).exit_code == 0
    assert runner.invoke(legacy, ['setup', '--list']).exit_code == 0
