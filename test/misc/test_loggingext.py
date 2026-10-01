import logging

import pytest

import lauschkiste.paths
from lauschkiste.misc import loggingext

OLD_STYLE = """
version: 1
filters:
  colorize:
    "()": jukebox.misc.loggingext.ColorFilter
    enable: False
handlers:
  file:
    class: logging.FileHandler
    filename: logs/app.log
    filters: [colorize]
loggers:
  jb:
    level: DEBUG
    handlers: [file]
    propagate: false
  jb.quiet:
    level: ERROR
"""


@pytest.fixture
def restore_logging():
    yield
    for name in ('lauschkiste', 'lauschkiste.quiet', 'jb', 'jb.quiet'):
        logger = logging.getLogger(name)
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
        logger.setLevel(logging.NOTSET)
        logger.propagate = True
    lauschkiste.paths.set_home(None)


def test_old_logger_configuration_still_configures_the_renamed_loggers(tmp_path, restore_logging):
    lauschkiste.paths.set_home(tmp_path)
    config = tmp_path / 'logger.yaml'
    config.write_text(OLD_STYLE)

    loggingext.configure_from_file(str(config))
    logging.getLogger('lauschkiste.some_module').info('hello from the renamed logger')
    logging.getLogger('lauschkiste.quiet').info('suppressed')

    assert logging.getLogger('lauschkiste.quiet').level == logging.ERROR
    log = (tmp_path / 'logs' / 'app.log').read_text()
    assert 'hello from the renamed logger' in log
    assert 'suppressed' not in log
