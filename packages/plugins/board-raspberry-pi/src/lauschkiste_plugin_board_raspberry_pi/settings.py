"""Settings of the board_raspberry_pi plugin (``plugins.board_raspberry_pi`` in the config)."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

SoundCard = Literal['none', 'max98357a', 'hifiberry-dac', 'hifiberry-dacplus', 'hifiberry-dacplushd',
                    'hifiberry-dacplusadc', 'hifiberry-dacplusadcpro', 'hifiberry-digi', 'hifiberry-digi-pro',
                    'hifiberry-amp']


class BoardSettings(BaseModel):
    sound_card: SoundCard = Field('none', title='Sound card (I²S)',
                                  description='An I²S sound card on the header; takes effect after '
                                              "'lauschctl setup raspi' and a reboot")
    onboard_audio: bool = Field(True, title='On-chip audio (headphone jack)',
                                description='Off with an external sound card (always off with an I²S sound card)')
    i2c: bool = Field(False, title='I²C', description='Also switched on for a battery sensor')
    spi: bool = Field(False, title='SPI', description='Also switched on for an RC522 reader')
    debug_mode: bool = Field(False, title='Debug mode', description='Log shutdown and reboot instead of doing them')
    hdmi_power_down: bool = Field(False, title='Switch HDMI off', description='Saves power without a display')
    wlan_power_save: Optional[bool] = Field(None, title='WLAN power saving',
                                            description='Off keeps the box reachable; empty leaves the system setting')
    wlan_interface: str = Field('wlan0', title='WLAN interface')
