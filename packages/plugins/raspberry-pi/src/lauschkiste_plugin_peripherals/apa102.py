"""APA102 RGB LEDs on two GPIO lines (data, clock), bit-banged."""

import mmap
import os
from typing import List, Sequence, Tuple

Color = Tuple[int, int, int]


def frame(pixels: Sequence[Color], brightness: int) -> bytes:
    """Start frame, one ``0xE0|brightness, blue, green, red`` per LED, end frame (a clock edge per two LEDs)."""
    level = 0xE0 | max(0, min(31, brightness))
    body = b''.join(bytes((level, blue, green, red)) for red, green, blue in pixels)
    return b'\x00' * 4 + body + b'\x00' * max(4, (len(pixels) + 15) // 16)


class LgpioWriter:
    """Shifts bytes out MSB first: data on ``data``, a rising edge on ``clock`` per bit."""

    def __init__(self, chip: int, data: int, clock: int):
        import lgpio
        self._lgpio = lgpio
        self._handle = lgpio.gpiochip_open(chip)
        try:
            lgpio.group_claim_output(self._handle, [data, clock], [0, 0])
        except Exception:
            lgpio.gpiochip_close(self._handle)
            raise
        self._group = data
        self._bits: List[Tuple[int, ...]] = [
            tuple(level for bit in range(7, -1, -1) for level in ((value >> bit) & 1, ((value >> bit) & 1) | 2))
            for value in range(256)]

    def write(self, data: bytes) -> None:
        write, handle, group, bits = self._lgpio.group_write, self._handle, self._group, self._bits
        for value in data:
            for level in bits[value]:
                write(handle, group, level)
        write(handle, group, 0)

    def close(self) -> None:
        self._lgpio.gpiochip_close(self._handle)


class GpiomemWriter:
    """Raspberry Pi up to model 4: the GPIO registers through /dev/gpiomem, no system call per bit
    (lgpio needs about ten times the CPU, too much for a level meter on a Pi Zero)."""

    FSEL, SET, CLEAR = 0x00, 0x1C, 0x28

    def __init__(self, chip: int, data: int, clock: int):
        if chip != 0 or data > 31 or clock > 31:
            raise OSError('only GPIO 0-31 of the first chip')
        try:
            with open('/proc/device-tree/model') as stream:
                if 'Raspberry Pi 5' in stream.read():
                    raise OSError('the Pi 5 has other GPIO registers')
        except FileNotFoundError:
            raise OSError('not a Raspberry Pi') from None
        fd = os.open('/dev/gpiomem', os.O_RDWR | os.O_SYNC)
        try:
            self._mem = mmap.mmap(fd, 4096, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
        finally:
            os.close(fd)
        for line in (data, clock):
            offset = self.FSEL + 4 * (line // 10)
            value = int.from_bytes(self._mem[offset:offset + 4], 'little')
            shift = 3 * (line % 10)
            value = (value & ~(0b111 << shift)) | (0b001 << shift)
            self._mem[offset:offset + 4] = value.to_bytes(4, 'little')
        data_bit, clock_bit = (1 << data).to_bytes(4, 'little'), (1 << clock).to_bytes(4, 'little')
        set_, clear = slice(self.SET, self.SET + 4), slice(self.CLEAR, self.CLEAR + 4)
        self._steps: List[Tuple[Tuple[slice, bytes], ...]] = []
        for value in range(256):
            steps = []
            for bit in range(7, -1, -1):
                steps += [(set_ if (value >> bit) & 1 else clear, data_bit), (set_, clock_bit), (clear, clock_bit)]
            self._steps.append(tuple(steps))

    def write(self, data: bytes) -> None:
        mem, steps = self._mem, self._steps
        for value in data:
            for register, bits in steps[value]:
                mem[register] = bits

    def close(self) -> None:
        self._mem.close()


def writer(chip: int, data: int, clock: int):
    """The fastest way to the LEDs on this board."""
    try:
        return GpiomemWriter(chip, data, clock)
    except (OSError, ValueError):
        return LgpioWriter(chip, data, clock)
