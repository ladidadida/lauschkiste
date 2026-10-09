#!/usr/bin/env python3
"""Generates the start and shutdown sounds of the box (``resources/audio``): soft bell-like notes, rising for the
start, falling for the shutdown. Nothing is sampled; the sounds are made from sine waves, so they belong to the project
(MIT, like the rest).

    ci/make_sounds.py           # writes packages/lauschkiste/src/lauschkiste/resources/audio/*.wav
"""

import math
import struct
import wave
from pathlib import Path

RATE = 44100
PEAK = 0.5  # of full scale: clearly audible, not loud
TARGET = Path(__file__).resolve().parent.parent / 'packages/lauschkiste/src/lauschkiste/resources/audio'

# C major pentatonic around C5: calm and cheerful
C5, D5, E5, G5, A5, C6 = 523.25, 587.33, 659.25, 783.99, 880.00, 1046.50


def bell(frequency: float, length: float, strength: float = 1.0):
    """One note: a quick soft attack, a bell-like decay, a little of the second and third harmonic."""
    count = int(RATE * length)
    out = []
    for n in range(count):
        t = n / RATE
        attack = min(1.0, t / 0.008)
        decay = math.exp(-t * 5.5)
        tone = (math.sin(2 * math.pi * frequency * t)
                + 0.35 * math.sin(2 * math.pi * 2 * frequency * t) * math.exp(-t * 9)
                + 0.12 * math.sin(2 * math.pi * 3 * frequency * t) * math.exp(-t * 14))
        out.append(strength * attack * decay * tone)
    return out


def melody(notes, step: float, tail: float):
    """Notes starting ``step`` seconds apart, ringing on for ``tail`` seconds after the last start."""
    total = int(RATE * (step * (len(notes) - 1) + tail))
    mix = [0.0] * total
    for index, (frequency, strength) in enumerate(notes):
        start = int(RATE * step * index)
        for n, value in enumerate(bell(frequency, tail, strength)):
            if start + n < total:
                mix[start + n] += value
    peak = max(abs(v) for v in mix) or 1.0
    fade = int(RATE * 0.05)
    for n in range(fade):  # no click at the very end
        mix[-1 - n] *= n / fade
    return [v / peak * PEAK for v in mix]


def write(path: Path, samples, channels: int) -> None:
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(channels)
        out.setsampwidth(2)
        out.setframerate(RATE)
        frames = bytearray()
        for value in samples:
            data = struct.pack('<h', int(max(-1.0, min(1.0, value)) * 32767))
            frames += data * channels
        out.writeframes(bytes(frames))


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    write(TARGET / 'startupsound.wav', melody([(C5, 0.9), (E5, 0.9), (G5, 0.9), (C6, 1.0)], 0.22, 1.1), 2)
    write(TARGET / 'shutdownsound.wav', melody([(G5, 0.9), (E5, 0.9), (C5, 1.0)], 0.24, 0.9), 1)


if __name__ == '__main__':
    main()
