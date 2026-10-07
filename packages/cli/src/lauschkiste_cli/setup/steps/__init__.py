from typing import List

from lauschkiste_cli.setup.base import Step
from lauschkiste_cli.setup.steps.extras import AudioStep, AutohotspotStep, KioskStep, MpdStep, SambaStep
from lauschkiste_cli.setup.steps.lauschkiste import PluginsStep, RfidStep, ServiceStep, WebPortStep
from lauschkiste_cli.setup.steps.system import BootStep, PackagesStep, RaspberryPiStep, WelcomeStep


def all_steps() -> List[Step]:
    """In the order they run (questions are asked in the same order)."""
    return [PackagesStep(), RaspberryPiStep(), MpdStep(), PluginsStep(), ServiceStep(), WebPortStep(), AudioStep(),
            SambaStep(), RfidStep(), KioskStep(), AutohotspotStep(), BootStep(), WelcomeStep()]
