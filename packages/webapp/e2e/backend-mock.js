export const backendData = {
  get_app_settings: { show_covers: false },
  get_folder_content: [
    {
      name: 'Albums',
      relpath: 'music/Rock/Albums',
      type: 'directory',
    },
    {
      name: 'sample.mp3',
      relpath: 'music/Rock/sample.mp3',
      type: 'file',
    },
  ],
  get_volume: 42,
  get_single_coverart: 'test-cover.png',
  list_albums: [
    { albumartist: 'Daft Punk', album: ['Discovery', 'Random Access Memories'] },
    { albumartist: 'Massive Attack', album: 'Mezzanine' },
  ],
  list_songs_by_artist_and_album: [
    {
      album: 'Bedtime Stories',
      artist: 'Storyteller',
      duration: 180,
      file: 'service:track:chapter-one',
      provider: 'streaming',
      title: 'Chapter One',
      track: '1',
    },
  ],
  list_cards: {
    '0001234567': {
      action: 'player.play',
      args: {},
      description: 'Start or resume playback.',
      error: null,
      ignore_card_removal_action: false,
      ignore_same_id_delay: false,
    },
  },
};

export const socketEvents = {
  'system.info': { version: '3.7.0-alpha', git_state: 'test', started_at: 'today' },
  'system.health': { cpu_temperature: 47.2, disk_total: 32_000_000_000, disk_used: 8_000_000_000,
    disk_free: 24_000_000_000 },
  'timers.changed': { name: 'stop_player', action: 'player.stop', args: {}, available: true,
    enabled: false, wait_seconds: 3600, remaining_seconds: 0 },
  'player.status': {
    album: 'Discovery',
    albumartist: null,
    artist: 'Daft Punk',
    cover_url: null,
    duration: 224,
    elapsed: 42,
    file: 'Daft Punk/Discovery/One More Time.mp3',
    playlist_length: 1,
    position: 0,
    provider: 'local_audio',
    random: false,
    repeat: false,
    single: false,
    state: 'play',
    title: 'One More Time',
    track: null,
  },
  'volume.level': { mute: false, volume: 42, soft_max_volume: 80 },
};

export async function mockBackend(
  page,
  {
    failApi = false,
    apiGate,
    showCovers = false,
    streamingLibrary = false,
    language = 'en',
  } = {},
) {
  const eventSockets = new Set();
  const libraryCalls = [];
  const apiCalls = [];
  const subscribedTopics = new Set();

  await page.addInitScript((lng) => {
    window.localStorage.setItem('i18nextLng', lng);
  }, language);

  const librarySources = () => [
    {
      id: 'local',
      label: 'Local',
      views: [
        {
          id: 'albums',
          label: 'Albums',
          kind: 'items',
          content_types: ['album'],
        },
        {
          id: 'folders',
          label: 'Folders',
          kind: 'folders',
          content_types: [],
        },
      ],
    },
    ...(streamingLibrary ? [{
      id: 'streaming',
      label: 'Streaming',
      views: [
        {
          id: 'playlists',
          label: 'Playlists',
          kind: 'items',
          content_types: ['playlist'],
        },
      ],
    }] : []),
  ];

  const libraryItems = (query) => {
    const localItems = backendData.list_albums.flatMap(entry => (
      (Array.isArray(entry.album) ? entry.album : [entry.album]).map(album => ({
        ...entry,
        album,
        content_type: 'album',
        provider: 'local',
      }))
    ));
    const streamingItems = streamingLibrary ? [{
      albumartist: 'Family',
      album: 'Bedtime Stories',
      content_type: 'playlist',
      content_uri: 'service:playlist:bedtime',
      provider: 'streaming',
    }] : [];
    const provider = query.get('provider');
    const contentTypes = query.getAll('content_types');
    return [...localItems, ...streamingItems].filter(item => (
      (!provider || item.provider === provider) &&
      (contentTypes.length === 0 || contentTypes.includes(item.content_type))
    ));
  };

  const getResponses = {
    '/api/v1/cards': () => backendData.list_cards,
    '/api/v1/library/entries': (query) => {
      libraryCalls.push(query.get('folder'));
      return { entries: backendData.get_folder_content };
    },
    '/api/v1/library/cover/album': () => ({ cover_url: backendData.get_single_coverart }),
    '/api/v1/library/cover/song': () => ({ cover_url: backendData.get_single_coverart }),
    '/api/v1/library/items': libraryItems,
    '/api/v1/library/sources': librarySources,
    '/api/v1/library/songs': () => backendData.list_songs_by_artist_and_album,
    '/api/v1/player/status': () => socketEvents['player.status'],
    '/api/v1/actions': () => [{ id: 'player.play', description: '', args: {} }],
    '/api/v1/settings': () => ({ show_covers: showCovers, on_screen_keyboard: true }),
    '/api/v1/settings/modules/audiobooks': () => ({
      name: 'audiobooks', kind: 'core', title: 'Audiobooks', restart_required: false,
      schema: { properties: { rewind_sec: { type: 'number', minimum: 0, maximum: 120, default: 10,
        title: 'Go back when continuing (seconds)' } } },
      values: { rewind_sec: 10 },
    }),
    '/api/v1/hardware': () => ({
      device: 'raspberry_pi', model: 'Raspberry Pi 3 Model B',
      pins: [
        { id: 'GPIO4', label: 'GPIO4 (pin 7)', position: 7, functions: ['gpio'],
          used_by: [{ owner: 'power_button', purpose: 'power off' }], conflict: false },
        { id: 'GPIO17', label: 'GPIO17 (pin 11)', position: 11, functions: ['gpio'],
          used_by: [{ owner: 'power_button', purpose: 'button' }, { owner: 'gpio_controls', purpose: 'button next' }],
          conflict: true },
        { id: 'GPIO27', label: 'GPIO27 (pin 13)', position: 13, functions: ['gpio'], used_by: [], conflict: false },
      ],
      interfaces: [{ id: 'i2c1', label: 'I²C 1', pins: ['GPIO2', 'GPIO3'], used_by: [{ owner: 'battery', purpose: 'MAX17048' }] }],
      conflicts: ['GPIO17'], unknown: [], boot_pending: ['i2c on'],
    }),
    '/api/v1/plugins': () => [
      { name: 'battery', enabled: false, running: false, package: 'lauschkiste-plugins-raspberry-pi', version: '0.1.0',
        summary: 'Battery monitor.', problem: null, missing_extras: [], needs: ['i2c'], provides: [],
        blocked: { missing: ['i2c'] }, detected: null, kind: 'hardware' },
      { name: 'device_raspberry_pi', enabled: false, running: false, package: 'lauschkiste-plugins-raspberry-pi',
        version: '0.1.0', summary: 'Raspberry Pi hardware.', problem: null, missing_extras: [], needs: [],
        provides: ['device', 'gpio', 'i2c'], blocked: null, detected: 'Raspberry Pi 3 Model B', kind: 'device' },
    ],
    '/api/v1/system/ip-addresses': () => ({ addresses: ['192.168.1.42'] }),
    '/api/v1/timers': () => [
      socketEvents['timers.changed'],
      { ...socketEvents['timers.changed'], name: 'fade_volume', action: 'volume.fade_out' },
      { ...socketEvents['timers.changed'], name: 'shutdown', action: 'hardware.shutdown', available: false },
    ],
    '/api/v1/volume': () => socketEvents['volume.level'],
    '/api/v1/volume/outputs': () => ({ active: 'primary', outputs: [
      { name: 'primary', alias: 'Built-in speakers', active: true },
      { name: 'secondary', alias: 'Bluetooth headset', active: false },
    ] }),
  };

  await page.route(
    url => url.pathname.startsWith('/api/v1/'),
    async route => {
      const request = route.request();
      const url = new URL(request.url());
      const method = request.method();
      apiCalls.push({
        method,
        path: url.pathname,
        body: method === 'GET' ? undefined : request.postDataJSON(),
      });

      if (apiGate) {
        await apiGate;
      }

      if (failApi) {
        await route.fulfill({
          body: JSON.stringify({ error: 'Backend unavailable' }),
          contentType: 'application/json',
          status: 503,
        });
        return;
      }

      const respond = method === 'GET' ? getResponses[url.pathname] : undefined;
      if (!respond) {
        await route.fulfill({ status: 204 });
        return;
      }
      await route.fulfill({
        body: JSON.stringify(respond(url.searchParams) ?? null),
        contentType: 'application/json',
        status: 200,
      });
    },
  );

  await page.route('**/cover-cache/test-cover.png', route => route.fulfill({
    contentType: 'image/png',
    path: 'public/logo192.png',
    status: 200,
  }));

  await page.routeWebSocket('**/api/v1/events', socket => {
    eventSockets.add(socket);
    socket.onMessage(message => {
      const payload = JSON.parse(message);
      if (payload.type !== 'subscribe') {
        return;
      }

      payload.topics.forEach(topic => {
        subscribedTopics.add(topic);
        const events = socketEvents;
        if (topic in events) {
          socket.send(JSON.stringify({
            type: 'event',
            topic,
            data: events[topic],
          }));
        }
      });
    });
  });

  const publishEvent = (topic, data) => {
    eventSockets.forEach(socket => {
      socket.send(JSON.stringify({
        type: 'event',
        topic,
        data,
      }));
    });
  };

  return {
    libraryCalls,
    publishEvent,
    apiCalls,
    subscribedTopics,
  };
}
