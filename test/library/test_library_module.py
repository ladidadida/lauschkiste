import time
from fractions import Fraction
from unittest.mock import Mock

import av
import pytest
from mutagen.flac import FLAC, Picture

from lauschkiste.cfghandler import ConfigHandler
from lauschkiste.contract.manager import ModuleManager
from lauschkiste.library.module import Library
from lauschkiste.player.module import Player
from lauschkiste.publishing.bus import EventBus

PNG = b'\x89PNG\r\n\x1a\n' + b'\x00' * 32


def write_flac(path, seconds=0.2, picture=None, **tags):
    path.parent.mkdir(parents=True, exist_ok=True)
    with av.open(str(path), 'w', format='flac') as container:
        stream = container.add_stream('flac', rate=8000)
        stream.layout = 'mono'
        samples = int(8000 * seconds)
        frame = av.AudioFrame(format='s16', layout='mono', samples=samples)
        frame.planes[0].update(bytes(frame.planes[0].buffer_size))
        frame.rate = 8000
        frame.time_base = Fraction(1, 8000)
        frame.pts = 0
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)
    audio = FLAC(str(path))
    for key, value in tags.items():
        audio[key] = value
    if picture is not None:
        pic = Picture()
        pic.mime = 'image/png'
        pic.data = picture
        audio.add_picture(pic)
    audio.save()


@pytest.fixture
def music(tmp_path):
    root = tmp_path / 'music'
    write_flac(root / 'Rock' / '02.flac', title='Second', artist='Band', album='Loud', tracknumber='2',
               albumartist='The Band')
    write_flac(root / 'Rock' / '01.flac', title='First', artist='Band', album='Loud', tracknumber='1',
               albumartist='The Band', picture=PNG)
    write_flac(root / 'Quiet' / 'song.flac', seconds=0.5, title='Lullaby', artist='Singer', album='Night')
    (root / 'Quiet' / 'cover.jpg').write_bytes(b'\xff\xd8\xff' + b'\x00' * 16)
    write_flac(root / 'Loose' / 'untagged.flac')
    return root


@pytest.fixture
def modules(tmp_path, music):
    ctrl = Mock()

    class TestPlayer(Player):
        def start(self, ctx):
            self._ctx = ctx
            self._coordinator = ctrl

        def ready(self):
            pass

        def stop(self):
            return []

    cfg = ConfigHandler('test')
    cfg.config_dict({'library': {'path': str(music), 'index': str(tmp_path / 'index.sqlite'),
                                 'cover_cache': str(tmp_path / 'covers')}})
    bus = EventBus()
    events = []
    bus.register(lambda topic, payload: events.append((topic, payload)))
    manager = ModuleManager([Library, TestPlayer], cfg, bus, plugins={}, strict=True)
    manager.load()
    manager.start()
    manager.ready()
    assert wait_for(lambda: any(topic == 'library.scanned' for topic, _ in events))
    yield manager, ctrl, events
    manager.stop()


def wait_for(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


def library(manager):
    return manager.handle('library')


def test_scan_indexes_tags_and_durations(modules):
    manager, _, events = modules
    scanned = [payload for topic, payload in events if topic == 'library.scanned']
    assert scanned[-1] == {'songs': 4, 'added': 4, 'updated': 0, 'removed': 0}

    song = library(manager).invoke('get_song', 'Quiet/song.flac')
    assert song.title == 'Lullaby'
    assert song.artist == 'Singer'
    assert song.duration == pytest.approx(0.5, abs=0.05)


def test_albums_and_songs_in_track_order(modules):
    manager, _, _ = modules
    items = library(manager).invoke('list_items')
    assert [(i.albumartist, i.album, i.provider) for i in items] == [
        ('Singer', 'Night', 'local'),
        ('The Band', 'Loud', 'local'),
    ]
    songs = library(manager).invoke('list_songs', 'The Band', 'Loud')
    assert [s.title for s in songs] == ['First', 'Second']
    assert songs[0].file == 'Rock/01.flac'


def test_song_lookup_accepts_absolute_paths(modules, music):
    manager, _, _ = modules
    song = library(manager).invoke('get_song', str(music / 'Rock' / '02.flac'))
    assert song.title == 'Second'
    assert library(manager).invoke('get_song', 'Rock/missing.flac') is None
    assert library(manager).invoke('get_song', 'http://radio.example/stream') is None


def test_search(modules):
    manager, _, _ = modules
    assert [s.title for s in library(manager).invoke('search', 'lulla')] == ['Lullaby']
    assert {s.file for s in library(manager).invoke('search', 'Rock/')} == {'Rock/01.flac', 'Rock/02.flac'}


def test_covers_from_embedded_picture_and_folder_image(modules, tmp_path):
    manager, _, _ = modules
    embedded = library(manager).invoke('get_song_cover', 'Rock/01.flac').cover_url
    assert embedded.startswith('/api/v1/library/covers/') and embedded.endswith('.png')
    assert (tmp_path / 'covers' / embedded.rsplit('/', 1)[1]).read_bytes() == PNG

    folder = library(manager).invoke('get_song_cover', 'Quiet/song.flac').cover_url
    assert folder.endswith('.jpg')
    assert library(manager).invoke('get_song_cover', 'Loose/untagged.flac').cover_url is None

    album = library(manager).invoke('get_album_cover', 'The Band', 'Loud').cover_url
    assert album == embedded


def test_rescan_picks_up_changes(modules, music):
    manager, _, events = modules
    write_flac(music / 'New' / 'new.flac', title='Fresh', album='New', artist='X')
    (music / 'Loose' / 'untagged.flac').unlink()
    events.clear()
    assert library(manager).invoke('refresh').scanning is True
    assert wait_for(lambda: any(topic == 'library.scanned' for topic, _ in events))
    scanned = [payload for topic, payload in events if topic == 'library.scanned'][-1]
    assert scanned == {'songs': 4, 'added': 1, 'updated': 0, 'removed': 1}


def test_player_plays_library_albums_as_files(modules):
    manager, ctrl, _ = modules
    ctrl.list_backends.return_value = ['local_audio']
    manager.handle('player').invoke('play_album', 'The Band', 'Loud', None, 'local')
    ctrl.play_files.assert_called_once_with(['Rock/01.flac', 'Rock/02.flac'])


def test_player_status_gets_library_metadata(modules, music):
    manager, _, _ = modules
    player = manager.instance('player')
    status = player._with_metadata(
        player.status.model(provider='local_audio', state='play', file=str(music / 'Rock' / '01.flac'), position=0))
    assert status.title == 'First'
    assert status.albumartist == 'The Band'
    assert status.cover_url.endswith('.png')
