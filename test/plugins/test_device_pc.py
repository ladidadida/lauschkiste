import lauschkiste_plugin_device_pc as device_plugin


def test_a_pc_is_detected_by_not_being_a_raspberry_pi():
    files = {'/sys/devices/virtual/dmi/id/product_name': 'ThinkPad T480\n'}
    assert device_plugin.DevicePcTest.detect(files.get) == 'ThinkPad T480'
    assert device_plugin.DevicePcTest.detect({}.get) == 'Computer'
    assert device_plugin.DevicePcTest.detect({'/proc/device-tree/model': 'Raspberry Pi 3 Model B'}.get) is None


def test_a_pc_provides_a_device_and_nothing_to_change_the_system():
    assert device_plugin.DevicePcTest.provides == ('device',)
