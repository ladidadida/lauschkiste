"""Raspberry Pi firmware state: throttling flags, HDMI and WLAN power."""

import logging
import subprocess
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger('lauschkiste.raspberry_pi.health')

# Bits of `vcgencmd get_throttled`
UNDER_VOLTAGE_NOW = 1 << 0
FREQUENCY_CAPPED_NOW = 1 << 1
THROTTLED_NOW = 1 << 2
UNDER_VOLTAGE_OCCURRED = 1 << 16
FREQUENCY_CAPPED_OCCURRED = 1 << 17
THROTTLED_OCCURRED = 1 << 18


class Throttled(BaseModel):
    raw: str
    under_voltage_now: bool
    frequency_capped_now: bool
    throttled_now: bool
    under_voltage_occurred: bool
    frequency_capped_occurred: bool
    throttled_occurred: bool


def parse_throttled(output: str) -> Throttled:
    """Parse ``throttled=0x50005`` as printed by ``vcgencmd get_throttled``."""
    value = output.strip().split('=', 1)[-1]
    flags = int(value, 16)
    return Throttled(
        raw=value,
        under_voltage_now=bool(flags & UNDER_VOLTAGE_NOW),
        frequency_capped_now=bool(flags & FREQUENCY_CAPPED_NOW),
        throttled_now=bool(flags & THROTTLED_NOW),
        under_voltage_occurred=bool(flags & UNDER_VOLTAGE_OCCURRED),
        frequency_capped_occurred=bool(flags & FREQUENCY_CAPPED_OCCURRED),
        throttled_occurred=bool(flags & THROTTLED_OCCURRED),
    )


def read_throttled() -> Optional[Throttled]:
    try:
        result = subprocess.run(['vcgencmd', 'get_throttled'], capture_output=True, text=True, timeout=3, check=True)
    except (OSError, subprocess.SubprocessError) as error:
        logger.debug(f"vcgencmd not available: {error}")
        return None
    return parse_throttled(result.stdout)


def run_quietly(command, description: str) -> None:
    try:
        subprocess.run(command, capture_output=True, timeout=5, check=True)
        logger.info(description)
    except (OSError, subprocess.SubprocessError) as error:
        logger.warning(f"{description} failed: {error}")


def hdmi_power_down() -> None:
    run_quietly(['vcgencmd', 'display_power', '0'], "HDMI output switched off")


def disable_wlan_power_save(interface: str) -> None:
    run_quietly(['sudo', 'iw', 'dev', interface, 'set', 'power_save', 'off'],
                f"WLAN power saving disabled on {interface}")
