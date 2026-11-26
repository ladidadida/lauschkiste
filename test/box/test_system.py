from lauschkiste.box.system import own_unit


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


def test_a_log_file_not_written_yet_or_switched_off_says_so(tmp_path):
    import logging
    import logging.handlers

    from lauschkiste.box.system import _read_log
    from lauschkiste.common import loggingext

    handler = logging.handlers.RotatingFileHandler(tmp_path / 'errors.log', delay=True)
    handler.name = 'error_file_handler'
    handler.setLevel(logging.WARNING)
    logger = logging.getLogger('lauschkiste')
    logger.addHandler(handler)
    try:
        assert _read_log('error_file_handler') == f"Nothing written to {tmp_path / 'errors.log'} in this run"
        assert not (tmp_path / 'errors.log').exists()
        loggingext.set_log_files('off')
        assert _read_log('error_file_handler').startswith('This log file is not written')
    finally:
        logger.removeHandler(handler)
        handler.close()
