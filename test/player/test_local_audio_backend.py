import array
import threading
import wave
from unittest.mock import Mock

import lauschkiste.library
from lauschkiste.audio_output import PortAudioSink, scale_volume
from lauschkiste.player.backends.local_audio import PlayerLocalAudio


class RecordingSink:
    """Test double for AudioSink: captures written PCM instead of opening a real device."""

    def __init__(self):
        self.opened_with = None
        self.chunks: list[bytes] = []
        self.closed = False

    def open(self, samplerate, channels):
        self.opened_with = (samplerate, channels)

    def write(self, data):
        self.chunks.append(data)

    def close(self):
        self.closed = True


class _FakeStatusStore(dict):
    def save_to_json(self):
        pass


def local_audio_backend(**attrs):
    """A PlayerLocalAudio with __init__ skipped (matches the PlayerMPD.__new__ test convention in
    test_mpd_backend_contract.py) -- avoids touching cfg/nv_manager/starting real threads."""
    backend = PlayerLocalAudio.__new__(PlayerLocalAudio)
    backend._cv = threading.Condition(threading.RLock())
    backend._abort = threading.Event()
    backend._queue = []
    backend._index = -1
    backend._position = 0.0
    backend._duration = None
    backend._state = 'stop'
    backend._random = False
    backend._repeat_mode = 'off'
    backend._volume = 100
    backend._last_played_folder = ''
    backend._status_store = _FakeStatusStore()
    backend._sink = RecordingSink()
    for name, value in attrs.items():
        setattr(backend, name, value)
    return backend


def write_wav(path, duration_s=0.2, rate=44100, channels=2, freq=440):
    n_frames = int(duration_s * rate)
    samples = array.array('h')
    for i in range(n_frames):
        value = int(1000 * ((i // 10) % 2 * 2 - 1))  # cheap non-zero square wave, not silence
        for _ in range(channels):
            samples.append(value)
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(samples.tobytes())


# -- scale_volume ------------------------------------------------------------------------------

def test_scale_volume_is_noop_at_full_volume():
    data = array.array('h', [1000, -1000]).tobytes()
    assert scale_volume(data, 100) == data


def test_scale_volume_scales_and_clamps():
    data = array.array('h', [1000, -1000]).tobytes()
    scaled = array.array('h')
    scaled.frombytes(scale_volume(data, 50))
    assert list(scaled) == [500, -500]


def test_scale_volume_zero_produces_silence():
    data = array.array('h', [1000, -1000]).tobytes()
    scaled = array.array('h')
    scaled.frombytes(scale_volume(data, 0))
    assert list(scaled) == [0, 0]


# -- _decode_track (real PyAV decode against a real WAV file) ----------------------------------

def test_decode_track_writes_pcm_and_advances_position(tmp_path):
    wav_path = tmp_path / 'track.wav'
    write_wav(wav_path, duration_s=0.2)
    backend = local_audio_backend()

    ended_naturally = backend._decode_track(str(wav_path), 0.0)

    assert ended_naturally is True
    assert backend._sink.opened_with == (44100, 2)
    assert backend._sink.closed is True
    assert len(backend._sink.chunks) > 0
    total_bytes = sum(len(c) for c in backend._sink.chunks)
    # 0.2s @ 44100 Hz, stereo, 16-bit -- allow the decoder a little slack either way.
    assert 0.15 * 44100 * 2 * 2 < total_bytes < 0.25 * 44100 * 2 * 2
    assert backend._position > 0.15


def test_decode_track_returns_false_when_aborted(tmp_path):
    wav_path = tmp_path / 'track.wav'
    write_wav(wav_path, duration_s=0.2)
    backend = local_audio_backend()
    backend._abort.set()

    assert backend._decode_track(str(wav_path), 0.0) is False
    assert backend._sink.chunks == []


def test_decode_track_missing_file_is_treated_as_ended():
    backend = local_audio_backend()
    assert backend._decode_track('/no/such/file.wav', 0.0) is True


def test_decode_track_corrupt_file_is_skipped_not_raised(tmp_path):
    # A file av.open() accepts but that blows up during decode (no audio stream here) must not
    # propagate out of _decode_track -- that would kill the whole playback worker thread.
    bogus = tmp_path / 'not_audio.wav'
    bogus.write_bytes(b'RIFF\x00\x00\x00\x00WAVEfmt ')
    backend = local_audio_backend()

    assert backend._decode_track(str(bogus), 0.0) is True


# -- play_folder builds the queue via PlaylistCollector -----------------------------------------

def test_play_folder_builds_queue_and_starts_playing(tmp_path, monkeypatch):
    (tmp_path / '01.mp3').touch()
    (tmp_path / '02.mp3').touch()
    monkeypatch.setattr(lauschkiste.library, 'root', lambda: str(tmp_path))
    backend = local_audio_backend()

    backend.play_folder('.')

    assert backend._queue == [str(tmp_path / '01.mp3'), str(tmp_path / '02.mp3')]
    assert backend._index == 0
    assert backend._state == 'play'
    assert backend._last_played_folder == '.'


def test_play_folder_with_no_content_stops(tmp_path, monkeypatch):
    monkeypatch.setattr(lauschkiste.library, 'root', lambda: str(tmp_path))
    backend = local_audio_backend()

    backend.play_folder('.')

    assert backend._queue == []
    assert backend._index == -1
    assert backend._state == 'stop'


# -- second swipe --------------------------------------------------------------------------------

def test_is_second_swipe_true_for_repeated_folder():
    backend = local_audio_backend(second_swipe_action=Mock(), _last_played_folder='stories')
    assert backend.is_second_swipe('stories') is True
    assert backend.is_second_swipe('other') is False


def test_is_second_swipe_false_without_configured_action():
    backend = local_audio_backend(second_swipe_action=None, _last_played_folder='stories')
    assert backend.is_second_swipe('stories') is False


def test_play_second_swipe_ignores_action_return_value():
    backend = local_audio_backend(second_swipe_action=Mock(return_value='ignored'))
    assert backend.play_second_swipe() is None


# -- status/playlist shape -----------------------------------------------------------------------

def test_playerstatus_shape():
    backend = local_audio_backend(
        _queue=['a.mp3', 'b.mp3'], _index=1, _position=12.5, _duration=180.0, _state='play', _volume=42)
    status = backend.playerstatus()
    assert status == {
        'state': 'play',
        'song': '1',
        'pos': '1',
        'file': 'b.mp3',
        'elapsed': '12.500',
        'duration': 180.0,
        'playlistlength': '2',
        'volume': '42',
        'random': '0',
        'repeat': '0',
        'single': '0',
        'provider': 'local_audio',
    }
    assert backend.get_current_song(None) == status


def test_playlistinfo_shape():
    backend = local_audio_backend(_queue=['a.mp3', 'b.mp3'])
    assert backend.playlistinfo() == [{'file': 'a.mp3', 'pos': '0'}, {'file': 'b.mp3', 'pos': '1'}]


# -- shuffle/repeat --------------------------------------------------------------------------------

def test_shuffle_toggle():
    backend = local_audio_backend()
    backend.shuffle('toggle')
    assert backend._random is True
    backend.shuffle('toggle')
    assert backend._random is False


def test_repeat_cycles_off_repeat_single():
    backend = local_audio_backend()
    backend.repeat('toggle')
    assert backend._repeat_mode == 'repeat'
    backend.repeat('toggle')
    assert backend._repeat_mode == 'single'
    backend.repeat('toggle')
    assert backend._repeat_mode == 'off'


# -- PortAudioSink falls back silently without a real device --------------------------------------

def test_portaudio_sink_falls_back_when_no_device(monkeypatch):
    import lauschkiste.audio_output as audio_output_module

    def raise_error(*args, **kwargs):
        raise RuntimeError("no output device")

    monkeypatch.setattr(audio_output_module.sd, 'RawOutputStream', raise_error)
    sink = PortAudioSink()

    sink.open(44100, 2)  # must not raise
    sink.write(b'\x00\x00')  # must not raise
    sink.close()  # must not raise


class FakeStream:
    def __init__(self, **kwargs):
        self.active = False
        self.events = []

    def start(self):
        self.active = True
        self.events.append('start')

    def write(self, data):
        assert self.active
        self.events.append(len(data))

    def stop(self):
        self.events.append('stop')

    def close(self):
        self.events.append('close')


def test_portaudio_sink_starts_after_prefill(monkeypatch):
    import lauschkiste.audio_output as audio_output_module
    streams = []
    monkeypatch.setattr(audio_output_module.sd, 'RawOutputStream', lambda **kw: streams.append(FakeStream()) or streams[-1])
    sink = PortAudioSink()
    sink.open(1000, 2)  # prefill: 300 frames = 1200 bytes

    sink.write(b'\x00' * 800)
    assert streams[0].events == []
    sink.write(b'\x00' * 800)
    assert streams[0].events == ['start', 1600]
    sink.write(b'\x00' * 400)
    sink.close()
    assert streams[0].events == ['start', 1600, 400, 'stop', 'close']


def test_portaudio_sink_plays_short_sounds_on_close(monkeypatch):
    import lauschkiste.audio_output as audio_output_module
    streams = []
    monkeypatch.setattr(audio_output_module.sd, 'RawOutputStream', lambda **kw: streams.append(FakeStream()) or streams[-1])
    sink = PortAudioSink()
    sink.open(1000, 2)
    sink.write(b'\x00' * 100)
    sink.close()
    assert streams[0].events == ['start', 100, 'stop', 'close']
