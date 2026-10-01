import threading

from jukebox.library.watch import FolderWatcher, snapshot


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


def test_watcher_calls_back_once_after_the_folder_settled(tmp_path):
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


def test_watcher_ignores_a_missing_root():
    watcher = FolderWatcher(lambda: '/does/not/exist', lambda: None, interval=0.01)
    watcher.start()
    watcher.stop().join(1)
