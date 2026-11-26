import logging

import pytest

import lauschkiste.common.paths
from lauschkiste.common import loggingext
from lauschkiste_cli.run import configured_log_files

CONFIG = '''version: 1
formatters:
  base:
    format: '{levelname} {message}'
    style: '{'
handlers:
  debug_file_handler:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: base
    filename: logs/app.log
    maxBytes: 100000
    backupCount: 1
  error_file_handler:
    class: logging.handlers.RotatingFileHandler
    level: WARNING
    formatter: base
    filename: logs/errors.log
    maxBytes: 100000
    backupCount: 1
  publisher:
    "()": {module}.PubStreamHandler
    level: WARNING
filters:
  colorize:
    "()": {module}.ColorFilter
loggers:
  lauschkiste:
    level: DEBUG
    handlers: [publisher, debug_file_handler, error_file_handler]
    propagate: false
'''


@pytest.fixture(autouse=True)
def restore_logging():
    loggers = [logging.getLogger(), *(logger for logger in logging.Logger.manager.loggerDict.values()
                                       if isinstance(logger, logging.Logger))]
    saved = [(logger, list(logger.handlers), logger.level, logger.disabled, logger.propagate) for logger in loggers]
    yield
    for logger in logging.Logger.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            for handler in logger.handlers:
                handler.close()
            logger.handlers = []
    for logger, handlers, level, disabled, propagate in saved:
        logger.handlers, logger.level, logger.disabled, logger.propagate = handlers, level, disabled, propagate


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(lauschkiste.common.paths, 'resolve', lambda value: tmp_path / value)
    return tmp_path


def configure(home, mode, module='lauschkiste.common.loggingext'):
    path = home / 'logger.yaml'
    path.write_text(CONFIG.replace('{module}', module))
    loggingext.configure_from_file(str(path), mode)
    for handler in logging.getLogger('lauschkiste').handlers:
        handler.flush()


def log_something():
    logger = logging.getLogger('lauschkiste.test')
    logger.debug('details')
    logger.warning('careful')
    for handler in logging.getLogger('lauschkiste').handlers:
        handler.flush()


@pytest.mark.parametrize('module', ['lauschkiste.misc.loggingext', 'lauschkiste.common.misc.loggingext'])
def test_a_configuration_naming_the_old_module_still_writes_the_files(home, module):
    configure(home, 'all', module)
    log_something()
    assert (home / 'logs' / 'app.log').read_text() == 'DEBUG details\nWARNING careful\n'
    assert (home / 'logs' / 'errors.log').read_text() == 'WARNING careful\n'


def test_errors_writes_only_the_error_file(home):
    configure(home, 'errors')
    log_something()
    assert not (home / 'logs' / 'app.log').exists()
    assert (home / 'logs' / 'errors.log').read_text() == 'WARNING careful\n'


def test_off_writes_no_file_at_all(home):
    (home / 'logs').mkdir()
    (home / 'logs' / 'app.log').write_text('before\n')
    configure(home, 'off')
    log_something()
    assert sorted(path.name for path in (home / 'logs').iterdir()) == ['app.log']
    assert (home / 'logs' / 'app.log').read_text() == 'before\n'


def test_the_files_can_be_switched_while_running(home):
    configure(home, 'all')
    log_something()
    loggingext.set_log_files('off')
    log_something()
    assert (home / 'logs' / 'errors.log').read_text() == 'WARNING careful\n'
    loggingext.set_log_files('errors')
    logging.getLogger('lauschkiste.test').error('broken')
    for handler in logging.getLogger('lauschkiste').handlers:
        handler.flush()
    assert (home / 'logs' / 'errors.log').read_text().endswith('ERROR broken\n')


def test_a_fresh_file_at_every_start_keeps_the_last_one_written(home):
    configure(home, 'errors')
    log_something()
    configure(home, 'errors')
    configure(home, 'errors')
    assert sorted(path.name for path in (home / 'logs').iterdir()) == ['errors.log.1']
    assert (home / 'logs' / 'errors.log.1').read_text() == 'WARNING careful\n'


@pytest.mark.parametrize('text, mode', [('system:\n  log_files: off\n', 'off'), ('system:\n  log_files: all\n', 'all'),
                                        ('system:\n  box_name: x\n', 'errors'), ('', 'errors'),
                                        ('system:\n  log_files: loud\n', 'errors')])
def test_the_setting_is_read_before_the_configuration_is_loaded(tmp_path, text, mode):
    conf = tmp_path / 'lauschkiste.yaml'
    conf.write_text(text)
    assert configured_log_files(conf) == mode
