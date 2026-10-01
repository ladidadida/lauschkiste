"""PCM output through sounddevice/PortAudio, shared by the local_audio backend and the jingle."""

import audioop
import logging

import av
import sounddevice as sd
from av.audio.resampler import AudioResampler

logger = logging.getLogger('lauschkiste.audio_output')

SAMPLE_RATE = 44100
CHANNELS = 2


def scale_volume(data: bytes, volume: int) -> bytes:
    """Scale packed s16 PCM by volume (0-100). No-op at full volume (the common case)."""
    if volume >= 100:
        return data
    return audioop.mul(data, 2, max(0, volume) / 100.0)


class AudioSink:
    """What a decoded track is written to. Exists so tests don't need a real audio device."""

    def open(self, samplerate: int, channels: int) -> None:
        raise NotImplementedError

    def write(self, data: bytes) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class PortAudioSink(AudioSink):
    """Real output via sounddevice/PortAudio. Falls back to silent (no-op) if no device is
    available -- e.g. the no-audio docker dev stack, or a CI box -- rather than raising and
    killing the daemon.

    The stream starts once ``PREFILL_SECONDS`` of audio are decoded, so the slow start of a track
    (opening and probing the file) doesn't empty the device buffer right away."""

    PREFILL_SECONDS = 0.3

    def __init__(self):
        self._stream = None
        self._pending = bytearray()
        self._prefill_bytes = 0

    def open(self, samplerate, channels):
        self._pending = bytearray()
        self._prefill_bytes = int(samplerate * self.PREFILL_SECONDS) * channels * 2
        try:
            self._stream = sd.RawOutputStream(samplerate=samplerate, channels=channels, dtype='int16')
        except Exception as e:
            logger.warning(f"No audio output device available ({e.__class__.__name__}: {e}); playing silently")
            self._stream = None

    def _write(self, data):
        try:
            if not self._stream.active:
                self._stream.start()
            self._stream.write(data)
        except Exception as e:
            logger.warning(f"Audio output error, playing silently for the rest of this track: {e}")
            self._stream = None

    def write(self, data):
        if self._stream is None:
            return
        if self._pending is not None:
            self._pending += data
            if len(self._pending) < self._prefill_bytes:
                return
            data, self._pending = bytes(self._pending), None
        self._write(data)

    def close(self):
        if self._stream is not None and self._pending:
            self._write(bytes(self._pending))
        self._pending = None
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None


def play_file(path: str, volume: int = 100, sink=None, should_stop=lambda: False) -> None:
    """Decode ``path`` and play it to the end (or until ``should_stop()``), blocking."""
    sink = sink or PortAudioSink()
    with av.open(path) as container:
        stream = container.streams.audio[0]
        resampler = AudioResampler(format='s16', layout='stereo', rate=SAMPLE_RATE)
        sink.open(SAMPLE_RATE, CHANNELS)
        try:
            for frame in container.decode(stream):
                for rframe in resampler.resample(frame):
                    if should_stop():
                        return
                    data = bytes(rframe.planes[0])[:rframe.samples * CHANNELS * 2]
                    sink.write(scale_volume(data, volume))
        finally:
            sink.close()
