import threading
import time
from types import SimpleNamespace

import pytest

from lauschkiste.player.backends import local_audio
from lauschkiste.player.backends.prefetch import Prefetch


def frame(seconds=0.5):
    return SimpleNamespace(samples=int(48000 * seconds), sample_rate=48000)


def test_frames_arrive_in_order_and_the_source_is_closed():
    closed = threading.Event()
    frames = [frame() for _ in range(5)]
    prefetch = Prefetch(iter(frames), 10, on_close=closed.set).start()
    assert list(prefetch) == frames
    assert closed.wait(1)


def test_reading_stops_when_the_buffer_is_full():
    read = []

    def source():
        for index in range(100):
            read.append(index)
            yield frame(1.0)

    prefetch = Prefetch(source(), 3).start()
    time.sleep(0.3)
    assert len(read) <= 5
    prefetch.stop()


def test_a_stalled_read_does_not_block_what_is_buffered():
    release = threading.Event()

    def source():
        yield frame()
        yield frame()
        release.wait(5)
        yield frame()

    iterator = iter(Prefetch(source(), 10).start())
    assert next(iterator) and next(iterator)
    release.set()
    assert next(iterator)


def test_an_error_of_the_source_reaches_the_player_after_the_buffer_is_drained():
    def source():
        yield frame()
        raise OSError('connection lost')

    iterator = iter(Prefetch(source(), 10).start())
    assert next(iterator)
    with pytest.raises(OSError):
        next(iterator)


def test_stop_ends_the_iteration_and_wait_ready_gives_up(monkeypatch):
    stop = threading.Event()

    def source():
        stop.wait(5)
        return
        yield

    prefetch = Prefetch(source(), 10).start()
    started = time.monotonic()
    prefetch.wait_ready(2, 0.3, lambda: False)
    assert time.monotonic() - started < 1
    prefetch.stop()
    assert list(prefetch) == []
    stop.set()


def test_a_stream_that_fails_to_open_is_tried_again(monkeypatch):
    monkeypatch.setattr(local_audio, 'RETRY_PAUSE', 0.01)
    backend = local_audio.PlayerLocalAudio.__new__(local_audio.PlayerLocalAudio)
    backend._abort = threading.Event()
    outcomes = iter(['failed', 'failed', 'ended'])
    backend._play_once = lambda path, position: next(outcomes)
    assert backend._decode_track('https://radio.example/stream', 0.0) is True
    assert list(outcomes) == []


def test_a_file_is_not_tried_again():
    backend = local_audio.PlayerLocalAudio.__new__(local_audio.PlayerLocalAudio)
    backend._abort = threading.Event()
    calls = []
    backend._play_once = lambda path, position: calls.append(path) or 'failed'
    assert backend._decode_track('/music/a.mp3', 0.0) is True
    assert len(calls) == 1


def test_an_abort_stops_the_retries(monkeypatch):
    monkeypatch.setattr(local_audio, 'RETRY_PAUSE', 5)
    backend = local_audio.PlayerLocalAudio.__new__(local_audio.PlayerLocalAudio)
    backend._abort = threading.Event()
    backend._abort.set()
    backend._play_once = lambda path, position: 'failed'
    assert backend._decode_track('https://radio.example/stream', 0.0) is False
