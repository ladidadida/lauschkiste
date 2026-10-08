"""PCM output through sounddevice/PortAudio, shared by the local_audio backend and the jingle."""

import audioop
import logging


logger = logging.getLogger('lauschkiste.audio_output')

SAMPLE_RATE = 44100
CHANNELS = 2


def volume_gain(volume: int) -> float:
    """Gain of a 0-100 volume setting. Cubic like PulseAudio's, so equal steps of the slider sound about
    equally loud: 50 % is -18 dB, not -6 dB as a linear gain would be."""
    return (max(0, min(100, volume)) / 100.0) ** 3


def scale_gain(data: bytes, gain: float) -> bytes:
    """Scale packed s16 PCM by ``gain``. No-op at full gain (the common case)."""
    if gain >= 1.0:
        return data
    return audioop.mul(data, 2, max(0.0, gain))


def scale_volume(data: bytes, volume: int) -> bytes:
    """Scale packed s16 PCM linearly by volume (0-100), e.g. a sound relative to the current output volume."""
    return scale_gain(data, volume / 100.0)


class AudioSink:
    """What a decoded track is written to. Exists so tests don't need a real audio device."""

    def open(self, samplerate: int, channels: int) -> None:
        raise NotImplementedError

    def write(self, data: bytes) -> None:
        raise NotImplementedError

    def close(self, discard: bool = False) -> float:
        """Stop the output; ``discard`` drops what is still buffered. Returns the dropped seconds."""
        raise NotImplementedError


class PortAudioSink(AudioSink):
    """Real output via sounddevice/PortAudio. Falls back to silent (no-op) if no device is
    available -- e.g. the no-audio docker dev stack, or a CI box -- rather than raising and
    killing the daemon.

    The stream starts once ``PREFILL_SECONDS`` of audio are decoded, so the slow start of a track
    (opening and probing the file) doesn't empty the device buffer right away."""

    PREFILL_SECONDS = 0.3
    #: A larger device buffer means fewer wake-ups: on a Pi Zero 0.3 s needs half the CPU of the default 35 ms
    LATENCY = 0.3
    #: Writes are collected to this length: fewer calls through PortAudio and ALSA
    CHUNK_SECONDS = 0.1

    def __init__(self):
        self._stream = None
        self._pending = bytearray()
        self._prefill_bytes = 0
        self._bytes_per_second = 1
        self._chunk = bytearray()
        #: ``callback(left, right, delay)``: RMS level (0..1) of each written chunk, audible in ``delay`` seconds
        self.level_callback = None

    def open(self, samplerate, channels):
        self._pending = bytearray()
        self._prefill_bytes = int(samplerate * self.PREFILL_SECONDS) * channels * 2
        self._bytes_per_second = samplerate * channels * 2
        self._chunk = bytearray()
        try:
            import sounddevice as sd
            self._stream = sd.RawOutputStream(samplerate=samplerate, channels=channels, dtype='int16',
                                              latency=self.LATENCY)
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
            return
        self._chunk += data
        if len(self._chunk) >= self._bytes_per_second * self.CHUNK_SECONDS:
            data, self._chunk = bytes(self._chunk), bytearray()
            self._write(data)
            self._report_level(data)

    def _report_level(self, data):
        callback = self.level_callback
        if callback is None or self._stream is None:
            return
        try:
            left = audioop.rms(audioop.tomono(data, 2, 1, 0), 2) / 32768
            right = audioop.rms(audioop.tomono(data, 2, 0, 1), 2) / 32768
            callback(left, right, self._stream.latency)
        except Exception as error:
            logger.debug(f"Level meter failed: {error}")

    def close(self, discard=False):
        dropped = 0.0
        if discard:
            dropped = (len(self._pending or b'') + len(self._chunk)) / self._bytes_per_second
        elif self._stream is not None and (self._pending or self._chunk):
            self._write(bytes(self._pending or b'') + bytes(self._chunk))
        self._pending = None
        self._chunk = bytearray()
        if self._stream is not None:
            try:
                if discard and self._stream.active:
                    dropped += self._stream.latency
                    self._stream.abort()
                else:
                    self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        return dropped


def play_file(path: str, volume: int = 100, sink=None, should_stop=lambda: False) -> None:
    """Decode ``path`` and play it to the end (or until ``should_stop()``), blocking."""
    import av
    from av.audio.resampler import AudioResampler

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
