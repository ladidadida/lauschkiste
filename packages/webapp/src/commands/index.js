const commands = {
  getSingleCoverArt: {
    rest: { method: 'GET', path: '/api/v1/library/cover/song' },
  },
  getAlbumCoverArt: {
    rest: { method: 'GET', path: '/api/v1/library/cover/album' },
  },
  librarySources: {
    rest: { method: 'GET', path: '/api/v1/library/sources' },
  },
  libraryItems: {
    rest: { method: 'GET', path: '/api/v1/library/items' },
  },
  songList: {
    rest: { method: 'GET', path: '/api/v1/library/songs' },
  },
  getSongByUrl: {
    rest: { method: 'GET', path: '/api/v1/library/song' },
    argKeys: ['song_url', 'provider']
  },
  librarySearch: {
    rest: { method: 'GET', path: '/api/v1/library/search' },
    argKeys: ['query'],
  },
  rfidLearn: {
    rest: { method: 'POST', path: '/api/v1/rfid/learn' },
    argKeys: ['seconds'],
  },
  rfidStopLearning: {
    rest: { method: 'POST', path: '/api/v1/rfid/learn/stop' },
  },
  cardsList: {
    rest: { method: 'GET', path: '/api/v1/cards' },
  },
  registerCard: {
    rest: { method: 'POST', path: '/api/v1/cards' },
  },
  deleteCard: {
    rest: { method: 'DELETE', path: '/api/v1/cards/{card_id}' },
  },
  playerstatus: {
    rest: { method: 'GET', path: '/api/v1/player/status' },
  },

  // Player Actions
  play: {
    rest: { method: 'POST', path: '/api/v1/player/play' },
    cardAction: 'player.play',
  },
  play_single: {
    rest: { method: 'POST', path: '/api/v1/player/song' },
    cardAction: 'player.play_single',
    argKeys: ['song_url', 'provider']
  },
  play_folder: {
    rest: { method: 'POST', path: '/api/v1/player/folder' },
    cardAction: 'player.play_folder',
    argKeys: ['folder']
  },
  play_album: {
    rest: { method: 'POST', path: '/api/v1/player/album' },
    cardAction: 'player.play_album',
    argKeys: ['albumartist', 'album', 'content_uri', 'provider']
  },
  pause: {
    rest: { method: 'POST', path: '/api/v1/player/pause' },
    cardAction: 'player.pause',
  },
  prev_song: {
    rest: { method: 'POST', path: '/api/v1/player/prev' },
    cardAction: 'player.prev',
  },
  next_song: {
    rest: { method: 'POST', path: '/api/v1/player/next' },
    cardAction: 'player.next',
  },
  toggle: {
    rest: { method: 'POST', path: '/api/v1/player/toggle' },
    cardAction: 'player.toggle',
  },
  shuffle: {
    rest: { method: 'POST', path: '/api/v1/player/shuffle' },
    cardAction: 'player.shuffle',
    argKeys: ['option'],
  },
  repeat: {
    rest: { method: 'POST', path: '/api/v1/player/repeat' },
    cardAction: 'player.repeat',
    argKeys: ['option'],
  },
  stop_after_current: {
    rest: { method: 'POST', path: '/api/v1/player/stop-after-current' },
    argKeys: ['enabled'],
  },
    seek: {
    // Renamed kwarg new_time -> position to match the REST body; only caller is seekbar.jsx.
    rest: { method: 'POST', path: '/api/v1/player/seek' },
    argKeys: ['position'],
  },

  // Audiobooks
  audiobooksList: {
    rest: { method: 'GET', path: '/api/v1/audiobooks' },
  },
  audiobook_play: {
    rest: { method: 'POST', path: '/api/v1/audiobooks/play' },
    cardAction: 'audiobooks.play',
    argKeys: ['book'],
  },
  audiobook_restart: {
    rest: { method: 'POST', path: '/api/v1/audiobooks/restart' },
    cardAction: 'audiobooks.restart',
    argKeys: ['book'],
  },
  audiobookSetFinished: {
    rest: { method: 'POST', path: '/api/v1/audiobooks/set_finished' },
    argKeys: ['book', 'finished'],
  },

  // Radio
  radioStations: {
    rest: { method: 'GET', path: '/api/v1/radio/stations' },
  },
  addRadioStation: {
    rest: { method: 'POST', path: '/api/v1/radio/stations' },
    argKeys: ['name', 'url', 'logo'],
  },
  updateRadioStation: {
    rest: { method: 'PUT', path: '/api/v1/radio/stations/{station}' },
    argKeys: ['station', 'name', 'url', 'logo'],
  },
  deleteRadioStation: {
    rest: { method: 'DELETE', path: '/api/v1/radio/stations/{station}' },
    argKeys: ['station'],
  },
  radio_play: {
    rest: { method: 'POST', path: '/api/v1/radio/play' },
    cardAction: 'radio.play',
    argKeys: ['station'],
  },

  // Podcasts
  podcastsList: {
    rest: { method: 'GET', path: '/api/v1/podcasts' },
  },
  podcastEpisodes: {
    rest: { method: 'GET', path: '/api/v1/podcasts/{podcast}/episodes' },
    argKeys: ['podcast'],
  },
  addPodcast: {
    rest: { method: 'POST', path: '/api/v1/podcasts' },
    argKeys: ['url', 'name'],
  },
  renamePodcast: {
    rest: { method: 'PUT', path: '/api/v1/podcasts/{podcast}' },
    argKeys: ['podcast', 'name'],
  },
  deletePodcast: {
    rest: { method: 'DELETE', path: '/api/v1/podcasts/{podcast}' },
    argKeys: ['podcast'],
  },
  refreshPodcasts: {
    rest: { method: 'POST', path: '/api/v1/podcasts/refresh' },
    argKeys: ['podcast'],
  },
  podcast_play: {
    rest: { method: 'POST', path: '/api/v1/podcasts/play' },
    cardAction: 'podcasts.play',
    argKeys: ['podcast', 'episode'],
  },
  podcastSetHeard: {
    rest: { method: 'POST', path: '/api/v1/podcasts/set_heard' },
    argKeys: ['podcast', 'episode', 'heard'],
  },

  // Volume
  getVolume: {
    rest: { method: 'GET', path: '/api/v1/volume' },
  },
  setVolume: {
    rest: { method: 'PUT', path: '/api/v1/volume' },
    argKeys: ['volume'],
  },
  setMaxVolume: {
    rest: { method: 'PUT', path: '/api/v1/volume/soft-max' },
    argKeys: ['max_volume'],
  },
  toggleMuteVolume: {
    rest: { method: 'POST', path: '/api/v1/volume/mute' },
  },
  change_volume: {
    rest: { method: 'POST', path: '/api/v1/volume/change' },
    cardAction: 'volume.change_volume',
    argKeys: ['step'],
  },
  getAudioOutputs: {
    rest: { method: 'GET', path: '/api/v1/volume/outputs' },
  },
  setAudioOutput: {
    rest: { method: 'PUT', path: '/api/v1/volume/outputs/active' },
    argKeys: ['name'],
  },
  toggle_output: {
    rest: { method: 'POST', path: '/api/v1/volume/outputs/toggle' },
    cardAction: 'volume.toggle_output',
  },

  // Timers
  listTimers: {
    rest: { method: 'GET', path: '/api/v1/timers' },
  },
  startTimer: {
    rest: { method: 'POST', path: '/api/v1/timers/start' },
    argKeys: ['timer', 'wait_seconds'],
  },
  cancelTimer: {
    rest: { method: 'POST', path: '/api/v1/timers/cancel' },
    argKeys: ['timer'],
  },
  timer_stop_player: {
    cardAction: 'timers.start',
    cardArgs: { timer: 'stop_player' },
    argKeys: ['wait_seconds'],
  },
  timer_fade_volume: {
    cardAction: 'timers.start',
    cardArgs: { timer: 'fade_volume' },
    argKeys: ['wait_seconds'],
  },
  timer_shutdown: {
    cardAction: 'timers.start',
    cardArgs: { timer: 'shutdown' },
    argKeys: ['wait_seconds'],
  },

  // System
  getIpAddresses: {
    rest: { method: 'GET', path: '/api/v1/system/ip-addresses' },
  },
  getSystemHealth: {
    rest: { method: 'GET', path: '/api/v1/system/health' },
  },
  say_my_ip: {
    rest: { method: 'POST', path: '/api/v1/system/say_my_ip' },
    cardAction: 'system.say_my_ip',
  },

  listActions: {
    rest: { method: 'GET', path: '/api/v1/actions' },
  },
  shutdown: {
    rest: { method: 'POST', path: '/api/v1/raspberry_pi/shutdown' },
    cardAction: 'raspberry_pi.shutdown',
  },
  reboot: {
    rest: { method: 'POST', path: '/api/v1/raspberry_pi/reboot' },
    cardAction: 'raspberry_pi.reboot',
  },

  // Misc
  getAppSettings: {
    rest: { method: 'GET', path: '/api/v1/settings' },
  },

  setAppSettings: {
    rest: { method: 'PUT', path: '/api/v1/settings' },
    argKeys: ['settings'],
  },
};

export default commands;
