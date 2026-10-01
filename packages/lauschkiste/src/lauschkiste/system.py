"""The system core module: version, logs, system information and web app settings."""

import logging
import logging.handlers
import os
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel

import lauschkiste
import lauschkiste.cfghandler
import lauschkiste.player
from lauschkiste.contract import CoreModule, OperationError, action, event, query
from lauschkiste.daemon import get_daemon

logger = logging.getLogger('lauschkiste.system')
cfg = lauschkiste.cfghandler.get_handler('lauschkiste')

LOG_TOPIC = 'system.log'


class SystemInfo(BaseModel):
    version: str
    git_state: str
    started_at: str


class LogMessage(BaseModel):
    message: str


class SystemHealth(BaseModel):
    cpu_temperature: Optional[float] = None
    disk_total: int
    disk_used: int
    disk_free: int


class IpAddresses(BaseModel):
    addresses: List[str]


def cpu_temperature() -> Optional[float]:
    """CPU temperature in °C from the first thermal zone, None where there is none."""
    for zone in sorted(Path('/sys/class/thermal').glob('thermal_zone*/temp')):
        try:
            return round(int(zone.read_text().strip()) / 1000.0, 1)
        except (OSError, ValueError):
            continue
    return None


def ip_addresses() -> List[str]:
    """Non-loopback IPv4 addresses of this machine."""
    try:
        output = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=2, check=True).stdout
        addresses = [a for a in output.split() if ':' not in a]
        if addresses:
            return addresses
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(('192.0.2.1', 9))
            return [probe.getsockname()[0]]
    except OSError:
        return []


class AppSettings(BaseModel):
    show_covers: bool = True


class AppSettingsUpdate(BaseModel):
    show_covers: Optional[bool] = None


def _read_log(handler_name: str) -> str:
    content = "No file handles configured"
    for h in logging.getLogger('lauschkiste').handlers:
        if not isinstance(h, logging.handlers.RotatingFileHandler):
            continue
        content = f"No file handler with name {handler_name} configured"
        if h.name != handler_name:
            continue
        try:
            if os.path.getsize(h.baseFilename) == 0:
                return (f"Log file {h.baseFilename} is empty. (Is the RotatingFileHandler configured as "
                        f"handler sink for jb in logger.yaml?)")
            mtime = os.path.getmtime(h.baseFilename)
            stime = get_daemon().start_time
            # 3 seconds tolerance between file creation and recording the start time
            if mtime - stime < -3:
                return (f"Log file {h.baseFilename} too old for this Jukebox start! "
                        f"Is the RotatingFileHandler configured as handler sink for jb in logger.yaml?")
            with open(h.baseFilename) as stream:
                return stream.read()
        except Exception as e:
            content = f"{e.__class__.__name__}: {e}"
            logger.error(content)
        break
    return content


class System(CoreModule):
    """Version information, log files and web app settings."""

    name = 'system'
    interface_version = '1.0'

    info = event('info', SystemInfo)
    health = event('health', SystemHealth)
    #: Published by lauschkiste.misc.loggingext.PubStreamHandler when configured in logger.yaml
    log = event('log', LogMessage)

    def __init__(self):
        self._ctx = None
        self._stop = threading.Event()
        self._health_thread: Optional[threading.Thread] = None

    def start(self, ctx) -> None:
        self._ctx = ctx
        ctx.publish(self.info, self.get_info())
        interval = float(ctx.config.get('health_interval_sec', default=10))
        if interval > 0:
            self._health_thread = threading.Thread(target=self._publish_health, args=(interval,),
                                                   name='system.health', daemon=True)
            self._health_thread.start()

    def stop(self):
        self._stop.set()
        return [self._health_thread] if self._health_thread is not None else []

    def _publish_health(self, interval: float) -> None:
        while True:
            try:
                self._ctx.publish(self.health, self.get_health())
            except Exception as error:
                logger.debug(f"Could not read system health: {error}")
            if self._stop.wait(interval):
                return

    @query(path='/info')
    def get_info(self) -> SystemInfo:
        """Version, git state and start time of the jukebox."""
        daemon = get_daemon()
        return SystemInfo(version=lauschkiste.version(), git_state=daemon.git_state,
                          started_at=time.ctime(daemon.start_time))

    @query(path='/health')
    def get_health(self) -> SystemHealth:
        """CPU temperature (where available) and disk usage of the music library's file system."""
        root = lauschkiste.player.get_music_library_path() or '/'
        path = Path(root).expanduser()
        usage = shutil.disk_usage(path if path.exists() else '/')
        return SystemHealth(cpu_temperature=cpu_temperature(), disk_total=usage.total, disk_used=usage.used,
                            disk_free=usage.free)

    @query(path='/ip-addresses')
    def get_ip_addresses(self) -> IpAddresses:
        """IPv4 addresses of this machine."""
        return IpAddresses(addresses=ip_addresses())

    @action()
    def say_my_ip(self) -> None:
        """Speak the IP address (needs espeak)."""
        addresses = ip_addresses()
        text = ' '.join(', '.join(address.split('.')) for address in addresses) or 'No network address'
        try:
            subprocess.Popen(['espeak', '-v', self._ctx.config.get('speech_voice', default='en'), text])
        except OSError as error:
            raise OperationError(501, 'no_speech', f'espeak is not available: {error}') from None

    @action()
    def restart_service(self) -> None:
        """Restart the jukebox systemd user service."""
        try:
            subprocess.Popen(['systemctl', '--user', 'restart', 'lauschkiste'])
        except OSError as error:
            raise OperationError(501, 'no_systemd', f'systemctl is not available: {error}') from None

    @query(path='/log')
    def get_log(self, kind: Literal['debug', 'error'] = 'debug') -> str:
        """Content of the debug or error log file of this run."""
        return _read_log(f'{kind}_file_handler')

    @query(path='/api/v1/settings')
    def get_app_settings(self) -> AppSettings:
        """Web app settings."""
        return AppSettings(show_covers=cfg.getn('webapp', 'show_covers', default=True))

    @action(method='PUT', path='/api/v1/settings')
    def set_app_settings(self, settings: AppSettingsUpdate) -> None:
        """Change web app settings; fields left out stay unchanged."""
        for key, value in settings.model_dump(exclude_none=True).items():
            cfg.setn('webapp', key, value=value)

    @action()
    def noop(self, message: str = '') -> None:
        """Do nothing (logs ``message`` as a warning if given)."""
        if message:
            logger.warning(message)
