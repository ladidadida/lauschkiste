"""APA102 RGB LEDs on two GPIO lines (data, clock), bit-banged through lgpio."""

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
