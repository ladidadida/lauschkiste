from lauschkiste.system import own_unit


def test_own_unit_is_read_from_the_cgroup(tmp_path):
    cgroup = tmp_path / 'cgroup'
    cgroup.write_text('0::/user.slice/user-1000.slice/user@1000.service/app.slice/lauschkiste-test.service\n')
    assert own_unit(str(cgroup)) == 'lauschkiste-test.service'
    cgroup.write_text('0::/user.slice/user-1000.slice/user@1000.service/app.slice/lauschkiste.service\n')
    assert own_unit(str(cgroup)) == 'lauschkiste.service'


def test_no_unit_outside_a_service(tmp_path):
    cgroup = tmp_path / 'cgroup'
    cgroup.write_text('0::/user.slice/user-1000.slice/user@1000.service/app.slice/app-gnome-terminal-1234.scope\n')
    assert own_unit(str(cgroup)) is None
    assert own_unit(str(tmp_path / 'missing')) is None
