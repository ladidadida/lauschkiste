import array
import threading
import wave
from unittest.mock import Mock

import pytest

import lauschkiste.library
from lauschkiste.audio_output import PortAudioSink, scale_gain, scale_volume, volume_gain
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

    def close(self, discard=False):
        self.closed = True
        return 0.0


@pytest.fixture(autouse=True)
def plain_sink(monkeypatch):
    """The soft start and end of the sink are tested on their own."""
    monkeypatch.setattr(PortAudioSink, 'LEAD_IN_SECONDS', 0)
    monkeypatch.setattr(PortAudioSink, 'FADE_IN_SECONDS', 0)
    monkeypatch.setattr(PortAudioSink, 'TAIL_SECONDS', 0)


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
    backend._stream_metadata = {}
    backend._state = 'stop'
    backend._random = False
    backend._repeat_mode = 'off'
    backend._ordered = False
    backend._stop_after_current = False
    backend._speed = 1.0
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

def test_volume_gain_is_cubic_like_pulseaudio():
    assert volume_gain(100) == 1.0 and volume_gain(0) == 0.0
    assert volume_gain(50) == pytest.approx(0.125)
    assert volume_gain(150) == 1.0 and volume_gain(-5) == 0.0
    assert all(volume_gain(v) < volume_gain(v + 1) for v in range(100))


def test_scale_gain_scales_the_samples():
    data = array.array('h', [1000, -1000]).tobytes()
    assert scale_gain(data, 1.0) is data
    scaled = array.array('h')
    scaled.frombytes(scale_gain(data, 0.125))
    assert list(scaled) == [125, -125]


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
        'stop_after_current': '0',
        'speed': '1.00',
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
    def raise_error(*args, **kwargs):
        raise RuntimeError("no output device")

    monkeypatch.setattr('sounddevice.RawOutputStream', raise_error)
    sink = PortAudioSink()

    sink.open(44100, 2)  # must not raise
    sink.write(b'\x00\x00')  # must not raise
    sink.close()  # must not raise


class FakeStream:
    def __init__(self, **kwargs):
        self.active = False
        self.events = []
        self.latency = kwargs.get('latency', 0.0)

    def start(self):
        self.active = True
        self.events.append('start')

    def write(self, data):
        assert self.active
        self.events.append(len(data))

    def stop(self):
        self.events.append('stop')

    def abort(self):
        self.events.append('abort')

    def close(self):
        self.events.append('close')


def test_portaudio_sink_starts_after_prefill(monkeypatch):
    streams = []
    monkeypatch.setattr('sounddevice.RawOutputStream', lambda **kw: streams.append(FakeStream()) or streams[-1])
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
    streams = []
    monkeypatch.setattr('sounddevice.RawOutputStream', lambda **kw: streams.append(FakeStream()) or streams[-1])
    sink = PortAudioSink()
    sink.open(1000, 2)
    sink.write(b'\x00' * 100)
    sink.close()
    assert streams[0].events == ['start', 100, 'stop', 'close']


def test_portaudio_sink_collects_small_writes(monkeypatch):
    streams = []
    monkeypatch.setattr('sounddevice.RawOutputStream', lambda **kw: streams.append(FakeStream(**kw)) or streams[-1])
    sink = PortAudioSink()
    sink.open(1000, 2)  # 4000 bytes/s: prefill 1200 bytes, chunks of 400 bytes
    sink.write(b'\x00' * 1200)
    sink.write(b'\x00' * 300)
    assert streams[0].events == ['start', 1200]
    sink.write(b'\x00' * 300)
    assert streams[0].events == ['start', 1200, 600]


def test_portaudio_sink_reports_the_level_of_each_channel(monkeypatch):
    import struct
    streams, levels = [], []
    monkeypatch.setattr('sounddevice.RawOutputStream', lambda **kw: streams.append(FakeStream(**kw)) or streams[-1])
    sink = PortAudioSink()
    sink.level_callback = lambda left, right, delay: levels.append((round(left, 2), right, delay))
    sink.open(1000, 2)
    sink.write(b'\x00' * 1200)
    sink.write(struct.pack('<200h', *([16384, 0] * 100)))
    assert levels == [(0.5, 0.0, streams[0].latency)]


def test_portaudio_sink_drops_buffered_audio_when_interrupted(monkeypatch):
    streams = []
    monkeypatch.setattr('sounddevice.RawOutputStream', lambda **kw: streams.append(FakeStream(**kw)) or streams[-1])
    sink = PortAudioSink()
    sink.open(1000, 2)
    sink.write(b'\x00' * 1600)
    sink.write(b'\x00' * 400)
    assert sink.close(discard=True) == streams[0].latency
    assert streams[0].events == ['start', 1600, 400, 'abort', 'close']

    sink.open(1000, 2)
    sink.write(b'\x00' * 400)
    assert sink.close(discard=True) == 0.1
    assert streams[1].events == ['stop', 'close']


def test_play_files_starts_at_entry_and_position(tmp_path, monkeypatch):
    monkeypatch.setattr(lauschkiste.library, 'root', lambda: str(tmp_path))
    backend = local_audio_backend()

    backend.play_files(['a/01.mp3', 'a/02.mp3'], 1, 42.5)

    assert backend._queue == [str(tmp_path / 'a' / '01.mp3'), str(tmp_path / 'a' / '02.mp3')]
    assert (backend._index, backend._position, backend._state) == (1, 42.5, 'play')

    backend.play_files(['a/01.mp3'], 5)
    assert (backend._index, backend._position) == (0, 0.0)


def test_ordered_files_ignore_shuffle_and_repeat_until_other_content(tmp_path, monkeypatch):
    monkeypatch.setattr(lauschkiste.library, 'root', lambda: str(tmp_path))
    backend = local_audio_backend()
    backend.shuffle('enable')
    backend.repeat('enable_repeat')

    backend.play_files(['a/01.mp3', 'a/02.mp3'], ordered=True)
    status = backend.playerstatus()
    assert (status['random'], status['repeat']) == ('0', '0')

    backend.play_single('b/song.mp3')
    status = backend.playerstatus()
    assert (status['random'], status['repeat']) == ('1', '1')


def test_stop_after_current_is_reported_and_cleared_by_stop():
    backend = local_audio_backend()
    backend.stop_after_current(True)
    assert backend.playerstatus()['stop_after_current'] == '1'
    backend.stop()
    assert backend.playerstatus()['stop_after_current'] == '0'


def test_play_single_resolves_library_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(lauschkiste.library, 'root', lambda: str(tmp_path))
    backend = local_audio_backend()
    backend.play_single('music/a/01.mp3')
    assert backend._queue == [str(tmp_path / 'music' / 'a' / '01.mp3')]
    backend.play_single('https://example.org/stream')
    assert backend._queue == ['https://example.org/stream']


def test_speed_applies_to_ordered_content_only(tmp_path, monkeypatch):
    monkeypatch.setattr(lauschkiste.library, 'root', lambda: str(tmp_path))
    backend = local_audio_backend()
    backend.set_speed(1.5)
    backend.play_files(['b/01.mp3'], ordered=True)
    assert backend.playerstatus()['speed'] == '1.50'
    backend.play_files(['m/01.mp3'])
    assert backend.playerstatus()['speed'] == '1.00'
    backend.set_speed(5)
    backend.play_files(['b/01.mp3'], ordered=True)
    assert backend.playerstatus()['speed'] == '2.00'


def test_jump_within_the_queue(tmp_path, monkeypatch):
    monkeypatch.setattr(lauschkiste.library, 'root', lambda: str(tmp_path))
    backend = local_audio_backend()
    backend.play_files(['a/1.mp3', 'a/2.mp3', 'a/3.mp3'])
    backend.jump(2)
    assert (backend._index, backend._position) == (2, 0.0)
    backend.jump(7)
    assert backend._index == 2


def test_decode_track_at_higher_speed_writes_less_audio(tmp_path):
    wav_path = tmp_path / 'tone.wav'
    write_wav(wav_path, duration_s=2.0)
    normal = local_audio_backend()
    normal._decode_track(str(wav_path), 0.0)
    fast = local_audio_backend(_ordered=True, _speed=1.5)
    fast._decode_track(str(wav_path), 0.0)

    normal_bytes = sum(len(c) for c in normal._sink.chunks)
    fast_bytes = sum(len(c) for c in fast._sink.chunks)
    assert fast_bytes == pytest.approx(normal_bytes / 1.5, rel=0.1)
    assert fast._position == pytest.approx(normal._position, rel=0.1)


def test_portaudio_sink_starts_and_ends_softly(monkeypatch):
    import struct
    monkeypatch.setattr(PortAudioSink, 'LEAD_IN_SECONDS', 0.1)
    monkeypatch.setattr(PortAudioSink, 'FADE_IN_SECONDS', 0.1)
    monkeypatch.setattr(PortAudioSink, 'TAIL_SECONDS', 0.05)
    written = []

    class Stream(FakeStream):
        def write(self, data):
            super().write(data)
            written.append(bytes(data))

    monkeypatch.setattr('sounddevice.RawOutputStream', lambda **kw: Stream(**kw))
    sink = PortAudioSink()
    sink.open(1000, 2)  # 4 bytes per frame
    loud = struct.pack('<h', 20000) * 2 * 1200
    sink.write(loud)
    sink.close()

    lead, music, tail = written
    assert lead == bytes(400) and tail == bytes(200)
    samples = struct.unpack(f'<{len(music) // 2}h', music)
    assert len(music) == len(loud)
    assert samples[0] == 0
    assert samples[0] < samples[50] < samples[100] < samples[150] < 20000
    assert all(sample == 20000 for sample in samples[200:])


def test_a_stream_reports_what_it_says_about_itself():
    backend = local_audio_backend(_queue=['http://radio/live'], _index=0, _state='play', _stream_metadata={
        'StreamTitle': 'Artist - Song', 'icy-name': 'Kinderlieder Radio', 'icy-genre': 'Kinderlieder',
        'icy-description': 'Songs fuer Kinder'})
    status = backend._status_dict()
    assert (status['title'], status['name'], status['genre'], status['description']) == (
        'Artist - Song', 'Kinderlieder Radio', 'Kinderlieder', 'Songs fuer Kinder')
    assert 'genre' not in local_audio_backend(_queue=['a.mp3'], _index=0)._status_dict()
