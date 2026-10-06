import threading
import time

import pytest

import lauschkiste.library.watch as watch
from lauschkiste.library.watch import FolderWatcher, snapshot


def test_snapshot_notices_new_files_folders_and_growing_files(tmp_path):
    (tmp_path / 'album').mkdir()
    song = tmp_path / 'album' / 'a.mp3'
    song.write_bytes(b'x')
    before = snapshot(str(tmp_path))
    assert snapshot(str(tmp_path)) == before

    song.write_bytes(b'xx')
    grown = snapshot(str(tmp_path))
    assert grown != before

    (tmp_path / 'album' / 'b.mp3').write_bytes(b'y')
    assert snapshot(str(tmp_path)) != grown

    (tmp_path / 'other').mkdir()
    assert str(tmp_path / 'other') in snapshot(str(tmp_path))


@pytest.fixture(params=['inotify', 'poll'])
def method(request, monkeypatch):
    if request.param == 'poll':
        def unavailable(root):
            raise OSError('not here')
        monkeypatch.setattr(watch, 'Inotify', unavailable)
    return request.param


def test_watcher_calls_back_once_after_the_folder_settled(tmp_path, method):
    calls = []
    changed = threading.Event()

    def on_change():
        calls.append(1)
        changed.set()

    watcher = FolderWatcher(lambda: str(tmp_path), on_change, interval=0.05)
    watcher.start()
    try:
        (tmp_path / 'new.mp3').write_bytes(b'x')
        assert changed.wait(2)
        changed.clear()
        assert not changed.wait(0.3)
        assert calls == [1]
    finally:
        watcher.stop().join(1)


def test_watcher_notices_files_in_new_subfolders(tmp_path, method):
    changed = threading.Event()
    watcher = FolderWatcher(lambda: str(tmp_path), changed.set, interval=0.05)
    watcher.start()
    try:
        (tmp_path / 'album').mkdir()
        assert changed.wait(2)
        time.sleep(0.2)
        changed.clear()
        (tmp_path / 'album' / 'song.mp3').write_bytes(b'x')
        assert changed.wait(2)
    finally:
        watcher.stop().join(1)


def test_watcher_stops_right_away(tmp_path, method):
    watcher = FolderWatcher(lambda: str(tmp_path), lambda: None, interval=30)
    watcher.start()
    time.sleep(0.1)
    started = time.monotonic()
    thread = watcher.stop()
    thread.join(5)
    assert not thread.is_alive() and time.monotonic() - started < 1


def test_watcher_ignores_a_missing_root():
    watcher = FolderWatcher(lambda: '/does/not/exist', lambda: None, interval=0.01)
    watcher.start()
    watcher.stop().join(1)
