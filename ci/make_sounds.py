#!/usr/bin/env python3
"""Generates the start and shutdown sounds of the box (``resources/audio``): a quick run of soft, wooden notes that
rises for the start and falls for the shutdown (the style ``glide`` is a single sliding tone instead).

Nothing is sampled; the sounds are made from sine waves, so they belong to the project (MIT, like the rest).

    ci/make_sounds.py                 # writes the sounds to packages/lauschkiste/src/lauschkiste/resources/audio
    ci/make_sounds.py glide DIR       # another style (glide or run) into another directory, e.g. to listen first
"""

import math
import struct
import sys
import wave
from pathlib import Path

RATE = 44100
PEAK = 0.45  # of full scale: clearly audible, not loud
TARGET = Path(__file__).resolve().parent.parent / 'packages/lauschkiste/src/lauschkiste/resources/audio'
C5, E5, G5, C6 = 523.25, 659.25, 783.99, 1046.50


def timbre(phase: float) -> float:
    """A round sine with a little brightness."""
    return math.sin(phase) + 0.25 * math.sin(2 * phase) + 0.08 * math.sin(3 * phase)


def glide(start: float, end: float, sweep: float, tail: float):
    """One tone that slides from ``start`` to ``end`` Hz in ``sweep`` seconds (exponentially, like a "boing") and then
    rings out for ``tail`` seconds."""
    total = int(RATE * (sweep + tail))
    out, phase = [], 0.0
    for n in range(total):
        t = n / RATE
        frequency = start * (end / start) ** min(1.0, t / sweep)
        phase += 2 * math.pi * frequency / RATE
        attack = min(1.0, t / 0.008)
        release = math.exp(-max(0.0, t - sweep * 0.55) * 9)
        out.append(attack * release * timbre(phase))
    return out


def run(notes, spacing: float, tail: float):
    """A quick run of soft, wooden notes ``spacing`` seconds apart."""
    total = int(RATE * (spacing * (len(notes) - 1) + tail))
    mix = [0.0] * total
    for index, frequency in enumerate(notes):
        start = int(RATE * spacing * index)
        for n in range(int(RATE * tail)):
            t = n / RATE
            value = (math.sin(2 * math.pi * frequency * t)
                     + 0.30 * math.sin(2 * math.pi * 4 * frequency * t) * math.exp(-t * 40)) \
                * min(1.0, t / 0.004) * math.exp(-t * 14)
            if start + n < total:
                mix[start + n] += value
    return mix


def normalized(samples):
    peak = max(abs(v) for v in samples) or 1.0
    fade = int(RATE * 0.03)
    out = [v / peak * PEAK for v in samples]
    for n in range(fade):  # no click at the very end
        out[-1 - n] *= n / fade
    return out


def write(path: Path, samples, channels: int) -> None:
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(channels)
        out.setsampwidth(2)
        out.setframerate(RATE)
        frames = bytearray()
        for value in samples:
            frames += struct.pack('<h', int(max(-1.0, min(1.0, value)) * 32767)) * channels
        out.writeframes(bytes(frames))


STYLES = {
    'glide': (lambda: glide(C5, C6, 0.26, 0.30), lambda: glide(C6, C5, 0.30, 0.34)),
    'run': (lambda: run([C5, E5, G5, C6], 0.085, 0.40), lambda: run([C6, G5, E5, C5], 0.10, 0.45)),
}


def main(argv) -> None:
    style = argv[1] if len(argv) > 1 else 'run'
    target = Path(argv[2]) if len(argv) > 2 else TARGET
    target.mkdir(parents=True, exist_ok=True)
    startup, shutdown = STYLES[style]
    write(target / 'startupsound.wav', normalized(startup()), 2)
    write(target / 'shutdownsound.wav', normalized(shutdown()), 1)


if __name__ == '__main__':
    main(sys.argv)
