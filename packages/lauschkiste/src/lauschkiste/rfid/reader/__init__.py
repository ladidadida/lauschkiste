"""RFID reader framework: one thread per configured reader, card dispatch, card removal detection.

Hardware drivers register at the ``rfid.readers`` extension point. Readers are configured in the
reader config file (``rfid.reader_config``), each with the name of its driver under ``module``.
"""

import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Protocol

from pydantic import BaseModel

import lauschkiste.cfghandler
import lauschkiste.legacy_actions as legacy_actions
import lauschkiste.paths
from lauschkiste.contract import CoreModule, event, extension_point, query

log = logging.getLogger('lauschkiste.rfid')

cfg_rfid = lauschkiste.cfghandler.get_handler('rfid')

DEFAULT_READER_CONFIG = 'settings/rfid.yaml'


class ReaderDriver(Protocol):
    def create_reader(self, reader_cfg_key: str) -> Any:
        """Return a reader for the reader config key: a context manager that iterates card ids
        ('' on timeout) and has ``stop()``."""


class CardDetected(BaseModel):
    card_id: str
    registered: bool


class CardRemovalTimer(threading.Thread):
    """Runs ``on_timeout`` once when the card has not been seen for about a second."""

    def __init__(self, on_timeout: Callable[[], Any], name: str):
        super().__init__(name=name, daemon=True)
        self.trigger = threading.Event()
        self.on_timeout = on_timeout

    def run(self):
        has_timed_out = True
        while True:
            time.sleep(0.2)
            self.trigger.wait(1)
            if self.trigger.is_set():
                has_timed_out = False
            else:
                if not has_timed_out:
                    self.on_timeout()
                has_timed_out = True


class ReaderRunner(threading.Thread):
    def __init__(self, reader_cfg_key: str, driver: ReaderDriver, rfid: 'Rfid'):
        super().__init__(name=f"{reader_cfg_key}Thread", daemon=True)
        self._key = reader_cfg_key
        self._driver = driver
        self._rfid = rfid
        self._logger = logging.getLogger(f'lauschkiste.rfid({reader_cfg_key})')
        self._reader = None
        self._cancel = threading.Event()
        self._same_id_delay = cfg_rfid.setndefault('rfid', 'readers', reader_cfg_key, 'same_id_delay', value=1.0)
        self._log_ignored = cfg_rfid.setndefault('rfid', 'readers', reader_cfg_key, 'log_ignored_cards',
                                                 value=False)
        place_not_swipe = cfg_rfid.setndefault('rfid', 'readers', reader_cfg_key, 'place_not_swipe', 'enabled',
                                               value=False)
        removal_entry = cfg_rfid.getn('rfid', 'readers', reader_cfg_key, 'place_not_swipe', 'card_removal_action',
                                      default=None)
        self._removal_timer = None
        if place_not_swipe:
            removal_action = rfid.resolve_config_action(removal_entry, f"{reader_cfg_key}.card_removal_action")
            if removal_action is None:
                self._logger.warning('place_not_swipe is enabled, but there is no valid card removal action. '
                                     'Ignoring place_not_swipe')
            else:
                self._removal_timer = CardRemovalTimer(removal_action, f"{reader_cfg_key}CRemover")
                self._removal_timer.start()

    def stop(self):
        self._cancel.set()
        if self._reader is not None:
            self._reader.stop()

    def run(self):  # noqa: C901
        self._reader = self._driver.create_reader(self._key)
        previous_id = ''
        previous_time = time.time()
        # Only for place-not-swipe: whether the card on the reader re-arms the removal timer
        valid_for_removal_action = False
        timer = self._removal_timer
        if timer is not None:
            timer.trigger.clear()

        with self._reader as reader:
            for card_id in reader:
                if self._cancel.is_set():
                    break
                if card_id:
                    if valid_for_removal_action and timer is not None and card_id == previous_id:
                        timer.trigger.set()
                    if card_id != previous_id or (time.time() - previous_time) >= self._same_id_delay:
                        self._logger.info(f"Received card id = '{card_id}'")
                        previous_id = card_id
                        valid_for_removal_action = False
                        card = self._rfid.lookup(card_id)
                        if card is not None:
                            if card.ignore_same_id_delay:
                                previous_id = ''
                            elif timer is not None:
                                valid_for_removal_action = not card.ignore_card_removal_action
                                if valid_for_removal_action:
                                    timer.trigger.set()
                        self._rfid.dispatch(card_id, card)
                    elif self._log_ignored:
                        self._logger.debug(f"Ignoring card id {card_id} due to same-card-delay "
                                           f"({self._same_id_delay}s)")
                    previous_time = time.time()
                self._cancel.wait(timeout=0.2)
                if timer is not None:
                    timer.trigger.clear()


class Rfid(CoreModule):
    """RFID readers: detect cards and run their actions."""

    name = 'rfid'
    interface_version = '1.0'
    requires = ('cards',)

    card_detected = event('card_detected', CardDetected)
    readers = extension_point('readers', ReaderDriver)

    def __init__(self):
        self._ctx = None
        self._runners: Dict[str, ReaderRunner] = {}

    def start(self, ctx) -> None:
        self._ctx = ctx
        path = str(lauschkiste.paths.resolve(ctx.config.get('reader_config', default=DEFAULT_READER_CONFIG)))
        try:
            lauschkiste.cfghandler.load_yaml(cfg_rfid, path)
        except FileNotFoundError:
            cfg_rfid.config_dict({'rfid': {'readers': {}}})
            log.warning(f"RFID reader config not found. Creating an empty one: '{path}'")
            cfg_rfid.save(only_if_changed=False)

    def ready(self) -> None:
        readers = cfg_rfid.getn('rfid', 'readers', default=None) or {}
        for key, reader_cfg in readers.items():
            driver_name = str(reader_cfg.get('module', '')).lower()
            if driver_name not in self.readers:
                log.error(f"Reader '{key}': no driver '{driver_name}' available. Enable its plugin "
                          f"('rfid_{driver_name}' under 'plugins:' in the Lauschkiste config).")
                continue
            log.info(f"Reader '{key}': using driver '{driver_name}'")
            self._runners[key] = ReaderRunner(key, self.readers.get(driver_name), self)
        for runner in self._runners.values():
            runner.start()

    def stop(self) -> List[threading.Thread]:
        for runner in self._runners.values():
            runner.stop()
        return list(self._runners.values())

    # -- used by the reader threads -------------------------------------------------------------

    def lookup(self, card_id: str):
        return self._ctx.modules.cards.get_card(card_id)

    def dispatch(self, card_id: str, card) -> None:
        self._ctx.publish(self.card_detected, CardDetected(card_id=card_id, registered=card is not None))
        if card is None:
            log.info(f"Unknown card: '{card_id}'")
            return
        self._ctx.actions.call_ignore_errors(card.action, card.args)

    def resolve_config_action(self, entry, where: str) -> Optional[Callable[[], Any]]:
        """Turn a configured action (new or old format) into a callable, or None if invalid."""
        return legacy_actions.bind_action(self._ctx.actions, entry, where, log)

    # -- operations -----------------------------------------------------------------------------

    @query(path='/readers')
    def list_readers(self) -> Dict[str, str]:
        """Configured readers and their driver."""
        readers = cfg_rfid.getn('rfid', 'readers', default=None) or {}
        return {key: str(value.get('module', '')) for key, value in readers.items()}
