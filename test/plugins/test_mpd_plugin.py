from unittest.mock import Mock

import pytest

pytest.importorskip('lauschkiste_plugin_mpd', reason="the mpd plugin package is not installed")

import lauschkiste.paths
import lauschkiste_plugin_mpd
import lauschkiste_plugin_mpd.backend
from lauschkiste.cfghandler import ConfigHandler
from lauschkiste.contract.manager import ModuleManager
from lauschkiste.library.module import Library
from lauschkiste.player.backend import PlayerBackend
from lauschkiste.player.module import Player
from lauschkiste.publishing.bus import EventBus


class PlayerWithoutLocalAudio(Player):
    def start(self, ctx):
        self._ctx = ctx
        self._configured_backend = ctx.config.setdefault('backend', value='local_audio')
        self.backends.on_register(self._add_backend)


def fake_backend_class(created):
    methods = {name: Mock() for name in vars(PlayerBackend) if not name.startswith('_')}

    class FakeMPD:
        def __init__(self, host, status_file):
            created.append((host, status_file))
            for name, mock in methods.items():
                setattr(self, name, mock)

    return FakeMPD


@pytest.mark.parametrize('config, expected_host', [
    ({'plugins': {'mpd': {'host': 'music.local'}}}, 'music.local'),
    ({'plugins': {'mpd': {}}, 'playermpd': {'host': 'legacy.local'}}, 'legacy.local'),
])
def test_mpd_plugin_registers_its_backend(monkeypatch, tmp_path, config, expected_host):
    created = []
    monkeypatch.setattr(lauschkiste_plugin_mpd.backend, 'PlayerMPD', fake_backend_class(created))
    monkeypatch.setattr(lauschkiste_plugin_mpd, 'cfg_main', _cfg(config))
    config = {**config, 'player': {'backend': 'mpd'},
              'library': {'path': str(tmp_path), 'index': str(tmp_path / 'index.sqlite'),
                          'cover_cache': str(tmp_path / 'covers'), 'scan_on_startup': False}}
    config['plugins']['mpd'].setdefault('library', {'update_on_startup': False, 'check_user_rights': False})

    cfg = _cfg(config)
    manager = ModuleManager([Library, PlayerWithoutLocalAudio], cfg, EventBus(),
                            plugins={'mpd': lambda: lauschkiste_plugin_mpd.Mpd}, strict=True)
    manager.load()
    manager.start()
    manager.ready()

    assert manager.failed == {}
    assert created == [(expected_host, str(lauschkiste.paths.resolve('settings/music_player_status.json')))]
    player = manager.instance('player')
    assert player.get_active_backend().name == 'mpd'
    sources = manager.handle('library').invoke('list_sources')
    assert [s.id for s in sources] == ['local', 'mpd']
    manager.stop()


def _cfg(data):
    cfg = ConfigHandler('test')
    cfg.config_dict(data)
    return cfg
