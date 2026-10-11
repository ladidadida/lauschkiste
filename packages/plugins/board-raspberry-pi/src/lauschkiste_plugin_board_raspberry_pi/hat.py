"""Boards on the 40-pin header that name themselves through their HAT EEPROM (``/proc/device-tree/hat``)."""

from pathlib import Path
from typing import Callable, NamedTuple, Optional

HAT_DIR = '/proc/device-tree/hat/'

#: (product contains, sound card setting), most specific first; HiFiBerry products only
HIFIBERRY = (
    ('dac2 hd', 'hifiberry-dacplushd'), ('dac+ hd', 'hifiberry-dacplushd'),
    ('adc pro', 'hifiberry-dacplusadcpro'), ('adc', 'hifiberry-dacplusadc'),
    ('digi+ pro', 'hifiberry-digi-pro'), ('digi+', 'hifiberry-digi'),
    ('dac+', 'hifiberry-dacplus'), ('amp2', 'hifiberry-dacplus'),
)


class Hat(NamedTuple):
    vendor: str
    product: str
    #: The matching ``sound_card`` setting, None for a board that is not a known sound card
    sound_card: Optional[str]

    @property
    def label(self) -> str:
        return f'{self.vendor} {self.product}'.strip()


def read_text(path: str) -> Optional[str]:
    try:
        return Path(path).read_text(errors='replace')
    except OSError:
        return None


def read_hat(read: Callable[[str], Optional[str]] = read_text) -> Optional[Hat]:
    """The attached HAT, None if there is none or it has no EEPROM."""
    vendor = (read(HAT_DIR + 'vendor') or '').strip('\x00\n ')
    product = (read(HAT_DIR + 'product') or '').strip('\x00\n ')
    if not vendor and not product:
        return None
    card = None
    if 'hifiberry' in vendor.lower():
        lowered = product.lower()
        card = next((setting for part, setting in HIFIBERRY if part in lowered), None)
    return Hat(vendor, product, card)
