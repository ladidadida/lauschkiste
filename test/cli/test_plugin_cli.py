import pytest
from typer.testing import CliRunner

import lauschkiste.cfghandler
import lauschkiste.paths
from lauschkiste_cli import plugin
from lauschkiste_cli.cli import ctl as app

runner = CliRunner()


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.delenv(lauschkiste.paths.env_name('CONF'), raising=False)
    monkeypatch.setenv(lauschkiste.paths.HOME_ENV, str(tmp_path))
    lauschkiste.paths.set_home(None)
    yield tmp_path
    lauschkiste.paths.set_home(None)


def enabled(home):
    cfg = lauschkiste.cfghandler.ConfigHandler('test-plugin-cli')
    lauschkiste.cfghandler.load_yaml(cfg, str(home / 'settings' / 'lauschkiste.yaml'))
    return dict(cfg.getn('plugins', default=None) or {})


def test_list_shows_bundled_plugins(home):
    result = runner.invoke(app, ['plugin', 'list'])
    assert result.exit_code == 0, result.output
    assert 'rfid_generic_usb' in result.output
    assert 'lauschkiste-plugin-rfid-readers' in result.output


def test_enable_and_disable(home):
    result = runner.invoke(app, ['plugin', 'enable', 'rfid_generic_usb'])
    assert result.exit_code == 0, result.output
    assert 'rfid_generic_usb' in enabled(home)
    assert 'enabled   rfid_generic_usb' in runner.invoke(app, ['plugin', 'list']).output

    config = (home / 'settings' / 'lauschkiste.yaml').read_text()
    assert config.count('#') > 0

    result = runner.invoke(app, ['plugin', 'disable', 'rfid_generic_usb'])
    assert result.exit_code == 0, result.output
    assert 'rfid_generic_usb' not in enabled(home)


def test_enable_unknown_plugin_fails(home):
    result = runner.invoke(app, ['plugin', 'enable', 'no_such_plugin'])
    assert result.exit_code == 1
    assert not (home / 'settings' / 'lauschkiste.yaml').exists()


def test_enable_with_extras_installs_them(home, monkeypatch):
    installed = []
    monkeypatch.setattr(plugin, 'install_requirements', installed.extend)
    result = runner.invoke(app, ['plugin', 'enable', 'rfid_rc522_spi', '--with-extras'])
    assert result.exit_code == 1 and 'needs spi, gpio' in result.output
    assert installed == []
    assert runner.invoke(app, ['plugin', 'enable', 'board_raspberry_pi']).exit_code == 0
    result = runner.invoke(app, ['plugin', 'enable', 'rfid_rc522_spi', '--with-extras'])
    assert result.exit_code == 0, result.output
    assert installed == ['lauschkiste-plugin-rfid-readers[rc522-spi]']
    assert 'rfid_rc522_spi' in enabled(home)
