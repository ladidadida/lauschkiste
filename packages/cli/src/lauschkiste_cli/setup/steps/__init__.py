from typing import List

from lauschkiste_cli.setup.base import Step
from lauschkiste_cli.setup.steps.device import DeviceStep
from lauschkiste_cli.setup.steps.extra_plugins import ExtraPluginsStep
from lauschkiste_cli.setup.steps.extras import AudioStep, AutohotspotStep, KioskStep, SambaStep
from lauschkiste_cli.setup.steps.lauschkiste import PluginsStep, RfidStep, ServiceStep, WebPortStep
from lauschkiste_cli.setup.steps.peripherals import PeripheralOptionsStep, PeripheralsStep
from lauschkiste_cli.setup.steps.system import PackagesStep, WelcomeStep


def all_steps() -> List[Step]:
    """In the order they run (questions are asked in the same order). The steps of the device plugin are added by
    ``device.with_device_steps``: its options right after the device, the boot configuration last because it follows
    from everything chosen."""
    return [DeviceStep(), PackagesStep(), PluginsStep(), ServiceStep(), WebPortStep(), AudioStep(), SambaStep(),
            KioskStep(), AutohotspotStep(), WelcomeStep(), ExtraPluginsStep(), PeripheralsStep(),
            PeripheralOptionsStep(), RfidStep()]
