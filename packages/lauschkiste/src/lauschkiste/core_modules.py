"""The core modules the daemon always starts. Order is irrelevant, ``requires`` decides."""

from lauschkiste.content.audiobooks import Audiobooks
from lauschkiste.content.cache import Cache
from lauschkiste.box.hardware import Hardware
from lauschkiste.box.input_devices import InputDevices
from lauschkiste.player.jingle import Jingle
from lauschkiste.content.library.module import Library
from lauschkiste.player.module import Player
from lauschkiste.content.podcasts import Podcasts
from lauschkiste.content.radio import Radio
from lauschkiste.rfid.cards import Cards
from lauschkiste.rfid.reader import Rfid
from lauschkiste.box.system import System
from lauschkiste.box.time_limits import TimeLimits
from lauschkiste.box.timers import Timers
from lauschkiste.player.volume import Volume

CORE_MODULES = [
    System,
    Hardware,
    Library,
    Player,
    Audiobooks,
    Cache,
    Radio,
    Podcasts,
    Volume,
    Timers,
    TimeLimits,
    Jingle,
    InputDevices,
    Cards,
    Rfid,
]
