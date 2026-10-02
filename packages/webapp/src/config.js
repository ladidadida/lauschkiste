const PUBSUB_ENDPOINT = '/api/v1/events';

const LOCAL_LIBRARY_SOURCE = 'local';
const PLAYER_STATUS_TOPIC = 'player.status';
const CARD_DETECTED_TOPIC = 'rfid.card_detected';
const LIBRARY_SCANNED_TOPIC = 'library.scanned';
const PODCASTS_TOPIC = 'podcasts.changed';
const RADIO_TOPIC = 'radio.changed';
const SYSTEM_INFO_TOPIC = 'system.info';
const SYSTEM_HEALTH_TOPIC = 'system.health';
const TIMERS_TOPIC = 'timers.changed';
const VOLUME_LEVEL_TOPIC = 'volume.level';

const BATTERY_TOPIC = 'raspberry_pi.battery';

const SUBSCRIPTIONS = [
  BATTERY_TOPIC,
  CARD_DETECTED_TOPIC,
  LIBRARY_SCANNED_TOPIC,
  PODCASTS_TOPIC,
  RADIO_TOPIC,
  SYSTEM_HEALTH_TOPIC,
  SYSTEM_INFO_TOPIC,
  TIMERS_TOPIC,
  VOLUME_LEVEL_TOPIC,
];

const ROOT_DIR = './';

// TODO: The reason why thos commands are empty objects is due to a legacy
// situation where titles associated with those commands were stored here
// After the intro of i18n, those titles became obsolete. Because changing
// the data structure from object to array requires some refactoring, this
// was not done yet to maintain functionality. It's ok to change the command
// object keys to arrays, but some downstream methods need to change as well
const ACTIONS_MAP = {
  // Command Aliases
  // Player
  play_music: {
    commands: {
      play_album: {},
      play_folder: {},
      play_single: {},
    }
  },

  audiobooks: {
    commands: {
      audiobook_play: {},
      audiobook_restart: {},
    },
  },

  radio: {
    commands: {
      radio_play: {},
    },
  },

  podcasts: {
    commands: {
      podcast_play: {},
    },
  },

  // Audio & Volume
  audio: {
    commands: {
      change_volume: {},
      toggle_output: {},
      play: {},
      pause: {},
      toggle: {},
      next_song: {},
      prev_song: {},
      shuffle: {},
      repeat: {},
    },
  },

  // System
  host: {
    commands: {
      shutdown: {},
      reboot: {},
      say_my_ip: {},
    }
  },

  // Timers
  timers: {
    commands: {
      timer_shutdown: {},
      timer_stop_player: {},
      timer_fade_volume: {},
    }
  },
}

const TIMER_STEPS = [0, 2, 5, 10, 15, 20, 30, 45, 60, 120, 180, 240];

export {
  BATTERY_TOPIC,
  CARD_DETECTED_TOPIC,
  ACTIONS_MAP,
  LIBRARY_SCANNED_TOPIC,
  LOCAL_LIBRARY_SOURCE,
  PLAYER_STATUS_TOPIC,
  PODCASTS_TOPIC,
  PUBSUB_ENDPOINT,
  RADIO_TOPIC,
  ROOT_DIR,
  SUBSCRIPTIONS,
  SYSTEM_HEALTH_TOPIC,
  SYSTEM_INFO_TOPIC,
  TIMERS_TOPIC,
  TIMER_STEPS,
  VOLUME_LEVEL_TOPIC,
}
