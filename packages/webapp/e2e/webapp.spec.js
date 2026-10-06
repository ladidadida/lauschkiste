import { expect, test } from '@playwright/test';

const backendData = {
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

const socketEvents = {
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

async function mockBackend(
  page,
  {
    failApi = false,
    apiGate,
    showCovers = false,
    streamingLibrary = false,
  } = {},
) {
  const eventSockets = new Set();
  const libraryCalls = [];
  const apiCalls = [];
  const subscribedTopics = new Set();

  await page.addInitScript(() => {
    window.localStorage.setItem('i18nextLng', 'en');
  });

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
    '/api/v1/settings': () => ({ show_covers: showCovers }),
    '/api/v1/settings/modules/audiobooks': () => ({
      name: 'audiobooks', kind: 'core', title: 'Audiobooks', restart_required: false,
      schema: { properties: { rewind_sec: { type: 'number', minimum: 0, maximum: 120, default: 10,
        title: 'Go back when continuing (seconds)' } } },
      values: { rewind_sec: 10 },
    }),
    '/api/v1/hardware': () => ({
      board: 'raspberry_pi', model: 'Raspberry Pi 3 Model B',
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
      { name: 'battery', enabled: false, running: false, package: 'lauschkiste-plugin-devices', version: '0.1.0',
        summary: 'Battery monitor.', problem: null, missing_extras: [], needs: ['i2c'], provides: [],
        blocked: { missing: ['i2c'] }, detected: null },
      { name: 'board_raspberry_pi', enabled: false, running: false, package: 'lauschkiste-plugin-board-raspberry-pi',
        version: '0.1.0', summary: 'Raspberry Pi hardware.', problem: null, missing_extras: [], needs: [],
        provides: ['board', 'gpio', 'i2c'], blocked: null, detected: 'Raspberry Pi 3 Model B' },
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

async function expectStableLayout(page) {
  await expect(page.locator('#root')).not.toBeEmpty();
  await expect(page.locator('.MuiBottomNavigation-root')).toBeVisible();

  const layout = await page.evaluate(() => {
    const actions = Array.from(
      document.querySelectorAll('.MuiBottomNavigationAction-root'),
      element => element.getBoundingClientRect(),
    );
    const nav = document.querySelector('.MuiBottomNavigation-root')
      .getBoundingClientRect();
    const actionRows = Array.from(document.querySelectorAll('.MuiListItem-root'));

    return {
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
      navWithinViewport: nav.top >= 0 && nav.bottom <= window.innerHeight + 1,
      overlappingContentActions: actionRows.some(row => {
        const text = row.querySelector('.MuiListItemText-root');
        const action = row.querySelector(
          '.MuiButton-root, .MuiIconButton-root, .MuiSwitch-root',
        );
        if (!text || !action) {
          return false;
        }

        const textRect = text.getBoundingClientRect();
        const actionRect = action.getBoundingClientRect();
        return (
          textRect.left < actionRect.right &&
          textRect.right > actionRect.left &&
          textRect.top < actionRect.bottom &&
          textRect.bottom > actionRect.top
        );
      }),
      overlappingActions: actions.some((action, index) => (
        actions.slice(index + 1).some(other => (
          action.left < other.right &&
          action.right > other.left &&
          action.top < other.bottom &&
          action.bottom > other.top
        ))
      )),
    };
  });

  expect(layout).toEqual({
    horizontalOverflow: false,
    navWithinViewport: true,
    overlappingContentActions: false,
    overlappingActions: false,
  });
}

async function expectAbove(top, bottom) {
  const [topBox, bottomBox] = await Promise.all([
    top.boundingBox(),
    bottom.boundingBox(),
  ]);

  expect(topBox.y + topBox.height).toBeLessThanOrEqual(bottomBox.y);
}

function collectConsoleErrors(page) {
  const errors = [];
  page.on('console', message => {
    if (message.type() === 'error') {
      errors.push(message.text());
    }
  });
  return errors;
}

const routes = [
  {
    name: 'player',
    path: '/',
    ready: '#player',
    text: 'One More Time',
  },
  {
    name: 'library',
    path: '/#/library/music/albums',
    ready: '#library',
    text: 'Discovery',
  },
  {
    name: 'cards',
    path: '/#/cards',
    ready: '#cards',
    text: '0001234567',
  },
  {
    name: 'settings',
    path: '/#/settings/status',
    ready: '#settings',
    text: '3.7.0-alpha',
  },
];

for (const route of routes) {
  test(`${route.name} route renders`, async ({ page }) => {
    const consoleErrors = collectConsoleErrors(page);
    await mockBackend(page);
    await page.goto(route.path);
    await expect(page.locator(route.ready)).toBeVisible();
    await expect(page.getByText(route.text, { exact: false }).first()).toBeVisible();
    await expectStableLayout(page);
    if (route.name === 'library') {
      await expectAbove(
        page.getByRole('tab', { name: 'Music' }),
        page.getByText('Discovery', { exact: true }),
      );
    }
    if (route.name === 'cards') {
      await expectAbove(
        page.getByRole('heading', { name: 'Cards' }),
        page.getByText('0001234567', { exact: true }),
      );
    }
    await expect(page).toHaveScreenshot(`${route.name}.png`);
    expect(consoleErrors).toEqual([]);
  });
}

test('bottom navigation changes routes', async ({ page }) => {
  const consoleErrors = collectConsoleErrors(page);
  await mockBackend(page);
  await page.goto('/');

  await page.getByRole('link', { name: 'Library' }).click();
  await expect(page).toHaveURL(/#\/library\/continue$/);

  await page.getByRole('link', { name: 'Settings' }).click();
  await expect(page).toHaveURL(/#\/settings$/);

  await page.getByRole('link', { name: /^Cards/ }).click();
  await page.getByRole('link', { name: 'Open the card list' }).click();
  await expect(page).toHaveURL(/#\/cards$/);
  await expect(page.getByRole('link', { name: 'Settings' })).toHaveClass(/Mui-selected/);
  expect(consoleErrors).toEqual([]);
});

test('player backdrop covers its full width across the md breakpoint', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop');
  const consoleErrors = collectConsoleErrors(page);
  await page.setViewportSize({ width: 800, height: 800 });
  await mockBackend(page, { showCovers: true });
  await page.goto('/');

  await expect(page.locator('#player img')).toBeVisible();
  for (const width of [800, 899, 900]) {
    await page.setViewportSize({ width, height: 800 });
    const [playerBox, backdropBox] = await Promise.all([
      page.locator('#player').boundingBox(),
      page.getByTestId('player-backdrop').boundingBox(),
    ]);

    expect(backdropBox.x).toBeCloseTo(playerBox.x, 0);
    expect(backdropBox.width).toBeCloseTo(playerBox.width, 0);
    expect(playerBox.width).toBeCloseTo(width < 900 ? width : width / 2, 0);
  }

  await page.setViewportSize({ width: 899, height: 800 });
  await expect(page).toHaveScreenshot('player-899.png');
  expect(consoleErrors).toEqual([]);
});

test('encoded library folder routes preserve the folder path', async ({ page }) => {
  const consoleErrors = collectConsoleErrors(page);
  const { libraryCalls } = await mockBackend(page);
  await page.goto('/#/library/music/folders/music%2FRock');

  await expect.poll(() => libraryCalls).toContain('music/Rock');
  await expect(page).toHaveURL(/#\/library\/music\/folders\/music%2FRock$/);
  await expect(page.getByRole('link', { name: 'Library' })).toHaveClass(/Mui-selected/);
  await expect(page.getByText('sample.mp3')).toBeVisible();
  await expectStableLayout(page);
  expect(consoleErrors).toEqual([]);
});

test('folder views stay within their type folder', async ({ page }) => {
  const consoleErrors = collectConsoleErrors(page);
  const { libraryCalls } = await mockBackend(page);
  await page.goto('/#/library/music/folders/..%2Fsettings');

  await expect(page).toHaveURL(/#\/library\/music\/folders\/music$/);
  await expect.poll(() => libraryCalls).toContain('music');
  expect(libraryCalls).not.toContain('../settings');
  expect(consoleErrors).toEqual([]);
});

test('music views replace the current nested route', async ({ page }) => {
  const consoleErrors = collectConsoleErrors(page);
  await mockBackend(page);
  await page.goto('/#/library/music/folders/music%2FRock?cardId=123');

  await page.getByRole('tab', { name: 'Albums' }).click();

  await expect(page).toHaveURL(/#\/library\/music\/albums\?cardId=123$/);
  await expect(page.getByText('Discovery', { exact: true })).toBeVisible();
  expect(consoleErrors).toEqual([]);
});

test('library playback preserves provider and content URI', async ({ page }) => {
  const consoleErrors = collectConsoleErrors(page);
  const { apiCalls } = await mockBackend(page, { streamingLibrary: true });
  await page.goto('/#/library/music/albums');

  await page.getByRole('button', { name: 'Streaming' }).click();
  await expect(page.getByText('Discovery', { exact: true })).toHaveCount(0);

  await page.getByText('Bedtime Stories', { exact: true }).click();
  await expect(page.getByText('Chapter One', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Play' }).click();

  await expect.poll(() => (
    apiCalls.find(call => call.path === '/api/v1/player/album')?.body
  )).toEqual({
    album: 'Bedtime Stories',
    albumartist: 'Family',
    content_uri: 'service:playlist:bedtime',
    provider: 'streaming',
  });
  expect(consoleErrors).toEqual([]);
});

test('cards route shows its loading state while the API is pending', async ({ page }) => {
  const consoleErrors = collectConsoleErrors(page);
  let releaseApi;
  const apiGate = new Promise(resolve => {
    releaseApi = resolve;
  });

  await mockBackend(page, { apiGate });
  await page.goto('/#/cards');

  await expect(page.getByRole('progressbar')).toBeVisible();
  releaseApi();
  await expect(page.getByText('0001234567')).toBeVisible();
  expect(consoleErrors).toEqual([]);
});

test('API failures leave navigation and an error state available', async ({ page }) => {
  await mockBackend(page, { failApi: true });
  await page.goto('/#/cards');

  await expect(page.getByText('An error occurred while loading cards list.')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Settings' })).toBeVisible();
  await expectStableLayout(page);
});

test('saving a card sends its action id and named arguments', async ({ page }) => {
  const consoleErrors = collectConsoleErrors(page);
  const { apiCalls } = await mockBackend(page);
  await page.goto('/#/cards/0001234567/edit');

  await page.getByRole('button', { name: 'Save' }).click();

  await expect.poll(() => (
    apiCalls.find(call => call.method === 'POST' && call.path === '/api/v1/cards')?.body
  )).toEqual({
    action: 'player.play',
    args: {},
    card_id: '0001234567',
    overwrite: true,
  });
  expect(consoleErrors).toEqual([]);
});

test('playback settings switch audio outputs and save module settings', async ({ page }) => {
  const consoleErrors = collectConsoleErrors(page);
  const { apiCalls } = await mockBackend(page);
  await page.goto('/#/settings/playback');

  const rewind = page.getByLabel('Go back when continuing (seconds)');
  await rewind.fill('25');
  await page.getByRole('button', { name: 'Save' }).first().click();
  await expect.poll(() => (
    apiCalls.find(call => call.method === 'PUT' && call.path === '/api/v1/settings/modules/audiobooks')?.body
  )).toEqual({ values: { rewind_sec: 25 } });

  await page.getByLabel('Bluetooth headset').check();
  await expect.poll(() => (
    apiCalls.find(call => call.method === 'PUT' && call.path === '/api/v1/volume/outputs/active')?.body
  )).toEqual({ name: 'secondary' });
  expect(consoleErrors).toEqual([]);
});

test('plugins can be switched on', async ({ page }) => {
  const consoleErrors = collectConsoleErrors(page);
  const { apiCalls } = await mockBackend(page);
  await page.goto('/#/settings/plugins');

  await expect(page.getByRole('switch', { name: 'battery on/off' })).toBeDisabled();
  await expect(page.getByText('Needs I²C. Switch on the board support of your board first.')).toBeVisible();
  await expect(page.getByText('Detected: Raspberry Pi 3 Model B')).toBeVisible();
  await page.getByRole('switch', { name: 'board_raspberry_pi on/off' }).click();
  await expect.poll(() => (
    apiCalls.find(call => call.method === 'PUT' && call.path === '/api/v1/plugins/board_raspberry_pi')?.body
  )).toEqual({ enabled: true });
  expect(consoleErrors).toEqual([]);
});

test('hardware page shows used pins, conflicts and pending boot changes', async ({ page }) => {
  const consoleErrors = collectConsoleErrors(page);
  await mockBackend(page);
  await page.goto('/#/settings/hardware');

  await expect(page.getByText('Raspberry Pi 3 Model B')).toBeVisible();
  await expect(page.getByText('I²C 1: battery: MAX17048')).toBeVisible();
  await expect(page.getByRole('cell', { name: 'power_button: button, gpio_controls: button next' })).toBeVisible();
  await expect(page.getByText('Used twice: GPIO17.', { exact: false })).toBeVisible();
  await expect(page.getByText('lauschctl setup raspi')).toBeVisible();
  await expect(page.getByRole('cell', { name: 'GPIO27 (pin 13)' })).toBeHidden();
  await page.getByRole('button', { name: 'Show 1 free pin' }).click();
  await expect(page.getByRole('cell', { name: 'GPIO27 (pin 13)' })).toBeVisible();
  expect(consoleErrors).toEqual([]);
});

test('hardware page offers a detected board when none is enabled', async ({ page }) => {
  const consoleErrors = collectConsoleErrors(page);
  const { apiCalls } = await mockBackend(page);
  await page.route('**/api/v1/hardware', route => route.fulfill({
    body: JSON.stringify({ board: null, model: null, pins: [], interfaces: [], conflicts: [], unknown: [],
      boot_pending: [], detected: [{ name: 'board_raspberry_pi', model: 'Raspberry Pi 3 Model B' }] }),
    contentType: 'application/json',
  }));
  await page.goto('/#/settings/hardware');

  await expect(page.getByText(/Detected: Raspberry Pi 3 Model B/)).toBeVisible();
  await page.getByRole('button', { name: 'Switch on' }).click();
  await expect.poll(() => (
    apiCalls.find(call => call.method === 'PUT' && call.path === '/api/v1/plugins/board_raspberry_pi')?.body
  )).toEqual({ enabled: true });
  await expect(page.getByText(/Board support switched on/)).toBeVisible();
  expect(consoleErrors).toEqual([]);
});

test('help pages open from the navigation and from settings hints', async ({ page }) => {
  const consoleErrors = collectConsoleErrors(page);
  await mockBackend(page);
  await page.goto('/');

  await page.getByRole('link', { name: 'Help' }).click();
  await expect(page).toHaveURL(/#\/help$/);
  await page.getByRole('link', { name: /Commands on the box/ }).click();
  await expect(page.getByRole('heading', { name: 'Commands on the box' })).toBeVisible();

  await page.goto('/#/settings/cards');
  await page.getByRole('link', { name: 'More in the help' }).click();
  await expect(page).toHaveURL(/#\/help\/lauschctl\?section=reader$/);
  await expect(page.locator('#reader')).toBeInViewport();
  expect(consoleErrors).toEqual([]);
});
