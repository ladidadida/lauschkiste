"""The core modules the daemon always starts. Order is irrelevant, ``requires`` decides."""

from lauschkiste.audiobooks import Audiobooks
from lauschkiste.input_devices import InputDevices
from lauschkiste.jingle import Jingle
from lauschkiste.library.module import Library
from lauschkiste.player.module import Player
from lauschkiste.podcasts import Podcasts
from lauschkiste.radio import Radio
from lauschkiste.rfid.cards import Cards
from lauschkiste.rfid.reader import Rfid
from lauschkiste.system import System
from lauschkiste.timers import Timers
from lauschkiste.volume import Volume

CORE_MODULES = [System, Library, Player, Audiobooks, Radio, Podcasts, Volume, Timers, Jingle, InputDevices, Cards, Rfid]
