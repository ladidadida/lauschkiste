"""Settings of the raspberry_pi plugin (``plugins.raspberry_pi`` in the config)."""

from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field

from lauschkiste.contract import ActionEntry

Pin = Field(ge=0, le=27, title='GPIO pin (BCM numbering)')


class GpioButton(BaseModel):
    pin: int = Pin
    on_press: Optional[ActionEntry] = Field(None, title='When pressed')
    on_hold: Optional[ActionEntry] = Field(None, title='When held')
    hold_time: float = Field(1.0, ge=0.1, le=10, title='Hold for (seconds)')
    pull_up: bool = Field(True, title='Internal pull-up', description='Off for buttons wired to 3.3 V')
    bounce_time: Optional[float] = Field(0.05, ge=0, le=1, title='Debounce (seconds)')


class RotaryEncoder(BaseModel):
    pin_a: int = Field(ge=0, le=27, title='GPIO pin A')
    pin_b: int = Field(ge=0, le=27, title='GPIO pin B')
    clockwise: Optional[ActionEntry] = Field(None, title='Turned clockwise')
    counter_clockwise: Optional[ActionEntry] = Field(None, title='Turned counter-clockwise')


class GpioSettings(BaseModel):
    enabled: bool = Field(False, title='Use GPIO')
    buttons: Dict[str, GpioButton] = Field(default_factory=dict, title='Buttons')
    rotary_encoders: Dict[str, RotaryEncoder] = Field(default_factory=dict, title='Rotary encoders')
    status_led: Optional[int] = Field(None, ge=0, le=27, title='Status LED pin',
                                      description='Lights up while Lauschkiste runs')


class BatterySettings(BaseModel):
    enabled: bool = Field(False, title='Battery monitor')
    driver: Literal['ina219', 'simulator'] = Field('ina219', title='Sensor')
    shunt_ohms: float = Field(0.1, gt=0, title='Shunt resistor (ohms)')
    empty_voltage: int = Field(3000, ge=0, title='Empty at (mV)')
    full_voltage: int = Field(4200, ge=0, title='Full at (mV)')
    warning_voltage: int = Field(3300, ge=0, title='Warn below (mV)')
    shutdown_voltage: int = Field(3000, ge=0, title='Shut down below (mV)')
    interval_sec: float = Field(10, ge=1, le=600, title='Measure every (seconds)')
    warning_action: Optional[ActionEntry] = Field(None, title='When the battery runs low')


class RaspberryPiSettings(BaseModel):
    debug_mode: bool = Field(False, title='Debug mode', description='Log shutdown and reboot instead of doing them')
    hdmi_power_down: bool = Field(False, title='Switch HDMI off', description='Saves power without a display')
    wlan_power_save: Optional[bool] = Field(None, title='WLAN power saving',
                                            description='Off keeps the box reachable; empty leaves the system setting')
    wlan_interface: str = Field('wlan0', title='WLAN interface')
    gpio: GpioSettings = Field(default_factory=GpioSettings, title='GPIO')
    battery: BatterySettings = Field(default_factory=BatterySettings, title='Battery')
