"""What config.txt needs for the hardware Lauschkiste is set up with; used by the board plugin
(to report pending changes) and by ``lauschctl setup raspi`` (to write them)."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from lauschkiste_plugin_board_raspberry_pi.pins import pin_id

SOUND_CARDS = {
    'max98357a': 'MAX98357A I²S amplifier',
    'hifiberry-dac': 'HiFiBerry DAC / MiniAmp (PCM5102A)',
    'hifiberry-dacplus': 'HiFiBerry DAC+ Standard/Pro/Amp2',
    'hifiberry-dacplushd': 'HiFiBerry DAC2 HD',
    'hifiberry-dacplusadc': 'HiFiBerry DAC+ ADC',
    'hifiberry-dacplusadcpro': 'HiFiBerry DAC+ ADC Pro',
    'hifiberry-digi': 'HiFiBerry Digi+',
    'hifiberry-digi-pro': 'HiFiBerry Digi+ Pro',
    'hifiberry-amp': 'HiFiBerry Amp+',
}
SOUND_OVERLAY = re.compile(r'^dtoverlay=(max98357a|hifiberry-[\w-]+)\s*$', re.MULTILINE)
AUDIO_ON = re.compile(r'^(dtparam=([^,\n]*,)*)audio=(on|true|yes|1)(.*)$', re.MULTILINE)
I2C_ON = re.compile(r'^dtparam=([^\n]*,)?i2c(_arm)?=on', re.MULTILINE)
SPI_ON = re.compile(r'^dtparam=([^\n]*,)?spi=on', re.MULTILINE)
POWEROFF = re.compile(r'^dtoverlay=gpio-poweroff[^\n]*$', re.MULTILINE)

I2C_BATTERY_DRIVERS = ('ina219', 'max17048')
SPI_READERS = ('rc522_spi',)
#: Device plugins of HATs with a DAC: the sound card they need
HAT_SOUND_CARDS = {'phat_beat': 'hifiberry-dac'}


@dataclass
class Wanted:
    sound_card: str = 'none'
    onboard_audio: bool = True
    i2c: bool = False
    spi: bool = False
    poweroff_pin: Optional[int] = None

    def poweroff_line(self) -> Optional[str]:
        if self.poweroff_pin is None:
            return None
        return f'dtoverlay=gpio-poweroff,gpiopin={self.poweroff_pin},active_low=1'


def _bcm(value: Any) -> Optional[int]:
    pin = pin_id(value) if value is not None else None
    return int(pin[4:]) if pin else None


def wanted(config: Mapping[str, Any], rfid: Optional[Mapping[str, Any]] = None) -> Wanted:
    """From the main config (and rfid.yaml): what the boot configuration should switch on."""
    plugins = config.get('plugins') or {}
    board = plugins.get('board_raspberry_pi') or {}
    battery = plugins.get('battery') or {}
    power = plugins.get('power_button') or {}
    readers = ((rfid or {}).get('rfid') or {}).get('readers') or {}
    card = str(board.get('sound_card') or 'none')
    if card == 'none':
        card = next((sound for hat, sound in HAT_SOUND_CARDS.items() if hat in plugins), 'none')
    return Wanted(
        sound_card=card if card in SOUND_CARDS else 'none',
        onboard_audio=card not in SOUND_CARDS and board.get('onboard_audio', True) is not False,
        i2c=bool(board.get('i2c')) or ('battery' in plugins
                                          and battery.get('driver', 'max17048') in I2C_BATTERY_DRIVERS),
        spi=bool(board.get('spi')) or any(str(r.get('module')) in SPI_READERS for r in readers.values()
                                           if isinstance(r, dict)),
        poweroff_pin=_bcm(power.get('poweroff_pin')) if 'power_button' in plugins else None,
    )


def pending(text: str, want: Wanted) -> List[str]:
    """What config.txt lacks."""
    problems = []
    if want.sound_card != 'none' and SOUND_OVERLAY.findall(text) != [want.sound_card]:
        problems.append(f'sound card {want.sound_card}')
    if not want.onboard_audio and AUDIO_ON.search(text):
        problems.append('on-chip audio off')
    if want.i2c and not I2C_ON.search(text):
        problems.append('I²C on')
    if want.spi and not SPI_ON.search(text):
        problems.append('SPI on')
    line = want.poweroff_line()
    if line and POWEROFF.findall(text) != [line]:
        problems.append(f'power-off pin GPIO{want.poweroff_pin}')
    return problems


def render(text: str, want: Wanted) -> str:
    """config.txt with what ``pending`` reports added; other lines stay."""
    if not want.onboard_audio:
        text = AUDIO_ON.sub(r'\1audio=off\4', text)
    additions: List[str] = []
    if want.sound_card != 'none' and SOUND_OVERLAY.findall(text) != [want.sound_card]:
        text = SOUND_OVERLAY.sub('', text)
        additions.append(f'dtoverlay={want.sound_card}')
    if want.i2c and not I2C_ON.search(text):
        additions.append('dtparam=i2c_arm=on')
    if want.spi and not SPI_ON.search(text):
        additions.append('dtparam=spi=on')
    line = want.poweroff_line()
    if line and POWEROFF.findall(text) != [line]:
        text = POWEROFF.sub('', text)
        additions.append(line)
    if additions:
        text = text.rstrip('\n') + '\n' + '\n'.join(additions) + '\n'
    return re.sub(r'\n{3,}', '\n\n', text)


def describe_cards() -> Dict[str, str]:
    return dict(SOUND_CARDS)
