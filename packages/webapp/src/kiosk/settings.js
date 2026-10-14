import { useContext } from 'react';

import { KIOSK_SETTINGS_TOPIC as SETTINGS_TOPIC, KIOSK_TOPIC } from '../config';
import PubSubContext from '../context/pubsub/context';

const OWN_APP = 'kiosk_standard';

// What the module sends until its first message arrives; the same as the defaults of its settings.
const DEFAULT_SETTINGS = {
  show_audiobooks: true,
  show_continue: true,
  show_music: true,
  show_podcasts: true,
  show_radio: true,
  show_volume: true,
  start_page: 'player',
  text_size: 'large',
  theme: 'night',
};

const useKioskSettings = () => {
  const { state } = useContext(PubSubContext);
  return { ...DEFAULT_SETTINGS, ...(state[SETTINGS_TOPIC] || {}) };
};

const useKioskState = () => useContext(PubSubContext).state[KIOSK_TOPIC];

export { DEFAULT_SETTINGS, OWN_APP, useKioskSettings, useKioskState };
