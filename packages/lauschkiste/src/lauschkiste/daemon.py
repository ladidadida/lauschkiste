# -*- coding: utf-8 -*-
import json
import threading
import os
import sys
import signal
import logging
import time
import atexit
from typing import (Optional)

import lauschkiste.paths
import lauschkiste.utils
import lauschkiste.publishing as publishing
from lauschkiste.api import FastApiServer
from lauschkiste.nv_manager import nv_manager

import lauschkiste
import lauschkiste.cfghandler

logger = logging.getLogger('jb.daemon')
cfg = lauschkiste.cfghandler.get_handler('lauschkiste')

#: Template a missing configuration_file is created from on first run (see JukeBox.__init__).
DEFAULT_CONFIG_TEMPLATE = str(lauschkiste.paths.resource('default-settings', 'lauschkiste.default.yaml'))

_SHUTDOWN_SIGNAL: Optional[int] = None


def shutdown_signal() -> Optional[int]:
    """The signal that started the shutdown (e.g. ``signal.SIGINT`` for Ctrl-C), None before."""
    return _SHUTDOWN_SIGNAL


@atexit.register
def log_active_threads():
    """This functions is registered with atexit very early, meaning it will be run very late. It is the best guess to
    evaluate which Threads are still running (and probably shouldn't be)

    This function is registered before all the components and their dependencies are loaded"""
    logger.debug(f"Active Threads = {threading.enumerate()}")


class JukeBox:
    def __init__(self, configuration_file: str, write_artifacts: bool):
        # Set up the signal listeners
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self._start_time = time.time()
        logger.info(f"Starting Jukebox Daemon (Version {lauschkiste.version()})")

        self._git_state = lauschkiste.utils.get_git_state()
        logger.info(f"Git state: {self._git_state}")

        self.nvm = nv_manager()
        self._signal_cnt = 0
        self.api_server = None
        self.modules = None
        lauschkiste.cfghandler.ensure_default_config(configuration_file, DEFAULT_CONFIG_TEMPLATE)
        lauschkiste.cfghandler.load_yaml(cfg, configuration_file)

        self.write_artifacts = write_artifacts

        logger.info("Welcome to " + cfg.getn('system', 'box_name', default='Jukebox Version 3'))
        logger.info(f"Time of start: {time.ctime(self._start_time)}")

    @property
    def start_time(self):
        return self._start_time

    @property
    def git_state(self):
        return self._git_state

    def signal_handler(self, esignal, frame):
        """Signal handler for orderly shutdown

        On first Ctrl-C (or SIGTERM) orderly shutdown procedure is embarked upon. It gets allocated a time-out!
        On third Ctrl-C (or SIGTERM), this is interrupted and there will be a hard exit!
        """
        # systemd: By default, a SIGTERM is sent, followed by 90 seconds of waiting followed by a SIGKILL.
        # Pressing Ctrl-C gives SIGINT
        global _SHUTDOWN_SIGNAL
        if _SHUTDOWN_SIGNAL is None:
            _SHUTDOWN_SIGNAL = esignal
        self._signal_cnt += 1
        # A further signal can interrupt this handler; decide on the count this call started with.
        count = self._signal_cnt
        # Below systemd's default stop timeout (90 s); a Pi Zero needs well over 5 s
        timeout: float = 30.0
        time_start = time.time_ns()
        msg = f"Received signal '{signal.Signals(esignal).name}'. Count = {count}"
        print(msg)
        logger.debug(msg)
        if count == 1:
            # Put the shutdown procedure into a thread, so we can make a time-out on it
            # Cannot use threading.Timer for the timeout, as sys.exit() must be called from main thread
            t = threading.Thread(target=self.exit_gracefully, args=[esignal, timeout], daemon=True, name="ShutdownThread")
            t.start()
            t.join(timeout)
            if t.is_alive():
                msg = f"Shutdown handler timed out after {timeout} s "
                print(f"Shutdown incomplete. {msg}. Terminating now forcefully!")
                print(f"Active Threads = {threading.enumerate()}")
                logger.error(msg)
                # Let's see which threads did not exit properly in time
                logger.error(f"Active Threads = {threading.enumerate()}")
                sys.exit(1)
            logger.info(f"Shutdown time: {((time.time_ns() - time_start) / 1000000.0):.3f} ms")
            sys.exit(0)
        elif count == 2:
            print("Waiting for closing down procedure to complete. Pressing Ctrl-C again will close Jukebox down immediately.")
        if count == 3:
            sys.exit(1)

    def exit_gracefully(self, esignal, timeout):
        msg = f"Closing down JukeBox {cfg.getn('system', 'box_name', default='Unnamed')}"
        print(msg)
        logger.info(msg)
        # (1) Stop taking commands
        if self.api_server is not None:
            self.api_server.terminate()
        # (2) Stop the music, then the modules in reverse start order
        thread_list = []
        if self.modules is not None:
            self.modules.catalog.call_ignore_errors('player.stop')
            thread_list = self.modules.stop()
        # (3) Save all nonvolatile data
        self.nvm.save_all()
        cfg.save(only_if_changed=True)
        # (4) Wait for the threads the modules handed back from stop()
        logger.debug(f"Waiting {timeout}s for module shutdown threads to complete: {thread_list}")
        for t in thread_list:
            t.join()

        logger.debug("All module shutdown threads closed")
        msg = "All done. Hear you soon!"
        print(msg)
        logger.info(msg)

    def run(self):
        time_start = time.time_ns()

        # Imported lazily: core modules import lauschkiste.daemon.get_jukebox_daemon at module level.
        from lauschkiste.contract.manager import ModuleManager
        from lauschkiste.core_modules import CORE_MODULES

        self.modules = ModuleManager(CORE_MODULES, cfg, publishing.get_bus())
        self.modules.load()
        self.modules.start()
        self.modules.ready()

        self.api_server = FastApiServer(modules=self.modules)
        self.api_server.start_and_wait()

        logger.info(f"Start-up time: {((time.time_ns() - time_start) / 1000000.0):.3f} ms")

        if self.write_artifacts:
            artifacts_dir = lauschkiste.paths.home() / 'artifacts'
            os.makedirs(artifacts_dir, exist_ok=True)
            with open(os.path.join(artifacts_dir, 'card_actions.json'), 'w') as stream:
                json.dump(self.modules.catalog.describe(), stream, indent=2)

        # Block the main thread until shutdown (exit_gracefully() calls api_server.terminate(),
        # which stops uvicorn and lets this thread finish).
        self.api_server.join()


class JukeBoxBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, *args, **kwargs):
        if not self._instance:
            self._instance = JukeBox(*args, **kwargs)
        return self._instance


_JUKEBOX_BUILDER: Optional[JukeBoxBuilder] = None


def get_jukebox_daemon(*args, **kwargs):
    global _JUKEBOX_BUILDER
    if _JUKEBOX_BUILDER is None:
        _JUKEBOX_BUILDER = JukeBoxBuilder()
    return _JUKEBOX_BUILDER(*args, **kwargs)
