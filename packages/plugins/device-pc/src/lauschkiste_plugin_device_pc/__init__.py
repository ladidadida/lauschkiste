"""Ordinary computers as the device: either left alone (a local test) or set up as a Lauschkiste box."""

from lauschkiste.contract import Plugin

DMI_PRODUCT = '/sys/devices/virtual/dmi/id/product_name'


def _is_raspberry_pi(read) -> bool:
    return 'Raspberry Pi' in (read('/proc/device-tree/model') or '')


class DevicePcTest(Plugin):
    """A PC or laptop used to try Lauschkiste out; the system is left as it is."""

    name = 'device_pc_test'
    title = 'PC or laptop, just trying it out'
    interface_version = '1.0'
    provides = ('device',)

    @classmethod
    def detect(cls, read):
        if _is_raspberry_pi(read):
            return None
        return (read(DMI_PRODUCT) or '').strip() or 'Computer'


class DevicePcBox(Plugin):
    """A PC, laptop or mini PC that is a Lauschkiste box of its own: it may be set up for that, also with a kiosk screen."""

    name = 'device_pc_box'
    title = 'PC, laptop or mini PC as a box of its own'
    interface_version = '1.0'
    provides = ('device', 'system_setup', 'autologin', 'screen')
