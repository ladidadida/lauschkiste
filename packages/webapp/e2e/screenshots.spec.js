import { test } from '@playwright/test';

import { backendData, mockBackend, socketEvents } from './backend-mock.js';

// Pictures for the documentation: `npx playwright test e2e/screenshots.spec.js --project=mobile`
// writes them to documentation/assets/screenshots/<language>/. The box is simulated, the content is made up.
const OUTPUT = '../../documentation/assets/screenshots';
const LANGUAGES = ['en', 'de'];

Object.assign(backendData, {
  get_folder_content: [
    { name: 'Gute-Nacht-Lieder', relpath: 'music/Gute-Nacht-Lieder', type: 'directory' },
    { name: 'Sing mit mir', relpath: 'music/Sing mit mir', type: 'directory' },
    { name: 'Tanz im Wald', relpath: 'music/Tanz im Wald', type: 'directory' },
  ],
  list_albums: [
    { albumartist: 'Die Sing-Gruppe', album: ['Sing mit mir', 'Gute-Nacht-Lieder'] },
    { albumartist: 'Familie Bär', album: ['Tanz im Wald', 'Frühlingslieder'] },
  ],
  list_cards: {
    '0004213377': { action: 'player.play_card', args: { folder: 'music/Sing mit mir' }, description: '',
      error: null, ignore_card_removal_action: false, ignore_same_id_delay: false },
    '0004213378': { action: 'audiobooks.play', args: { book: 'Die kleine Eule' }, description: '',
      error: null, ignore_card_removal_action: false, ignore_same_id_delay: false },
    '0004213379': { action: 'player.toggle', args: {}, description: '',
      error: null, ignore_card_removal_action: false, ignore_same_id_delay: false },
  },
});
Object.assign(socketEvents['player.status'], {
  album: 'Sing mit mir', artist: 'Die Sing-Gruppe', title: 'Der Mond ist aufgegangen', elapsed: 42, duration: 168,
  file: 'Sing mit mir/01 Der Mond ist aufgegangen.mp3',
});

const pages = [
  { name: 'player', path: '/' },
  { name: 'library', path: '/#/library/music/albums' },
  { name: 'upload', path: '/#/library/music/folders/music' },
  { name: 'cards', path: '/#/cards' },
  { name: 'settings', path: '/#/settings' },
];

for (const language of LANGUAGES) {
  test(`documentation screenshots (${language})`, async ({ page }) => {
    await mockBackend(page, { language, showCovers: true });
    for (const { name, path } of pages) {
      await page.goto(path);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(800);
      await page.screenshot({ path: `${OUTPUT}/${language}/${name}.png` });
    }
  });
}
