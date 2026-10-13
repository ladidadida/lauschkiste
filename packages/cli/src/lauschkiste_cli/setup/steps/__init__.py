from typing import List

from lauschkiste_cli.setup.base import Step
from lauschkiste_cli.setup.steps.device import DeviceStep
from lauschkiste_cli.setup.steps.extra_plugins import ExtraPluginsStep
from lauschkiste_cli.setup.steps.hardware import HardwareStep
from lauschkiste_cli.setup.steps.extras import AudioStep, AutohotspotStep, KioskStep, SambaStep
from lauschkiste_cli.setup.steps.lauschkiste import PluginsStep, RfidStep, ServiceStep, WebPortStep
from lauschkiste_cli.setup.steps.peripherals import PeripheralOptionsStep, PeripheralsStep
from lauschkiste_cli.setup.steps.system import BootStep, PackagesStep, RaspberryPiStep, WelcomeStep


def all_steps() -> List[Step]:
    """In the order they run (questions are asked in the same order): the device and its options, then what is
    attached to it and its options. The boot configuration comes last because it follows from everything chosen."""
    return [DeviceStep(), PackagesStep(), HardwareStep(), PluginsStep(), ServiceStep(), WebPortStep(), AudioStep(),
            SambaStep(), KioskStep(), AutohotspotStep(), BootStep(), WelcomeStep(),
            ExtraPluginsStep(), PeripheralsStep(), PeripheralOptionsStep(), RfidStep(), RaspberryPiStep()]
