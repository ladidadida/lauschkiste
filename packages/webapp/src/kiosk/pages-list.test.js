import { describe, expect, it } from 'vitest';

import { startPage, visiblePages } from './pages-list';
import { DEFAULT_SETTINGS } from './settings';
import { DEFAULTS, kioskTheme, themeUrl } from './theme';

describe('pages', () => {
  it('offers the player and every section that is switched on', () => {
    const settings = { ...DEFAULT_SETTINGS, show_radio: false, show_continue: false };
    expect(visiblePages(settings).map(({ id }) => id)).toEqual(['player', 'music', 'audiobooks', 'podcasts']);
  });

  it('starts at the player or the first section', () => {
    expect(startPage(DEFAULT_SETTINGS)).toBe('player');
    expect(startPage({ ...DEFAULT_SETTINGS, start_page: 'library' })).toBe('continue');
    expect(startPage({ ...DEFAULT_SETTINGS, start_page: 'library', show_continue: false })).toBe('music');
  });

  it('starts at the player when no section is offered', () => {
    const none = {
      ...DEFAULT_SETTINGS, show_continue: false, show_music: false, show_audiobooks: false, show_radio: false,
      show_podcasts: false, start_page: 'library',
    };
    expect(startPage(none)).toBe('player');
  });
});

describe('theme', () => {
  it('builds the MUI theme from the variables of a theme file', () => {
    const theme = kioskTheme({ ...DEFAULTS, mode: 'light', accent: '#ff0000', radius: '30px' }, 'huge');
    expect(theme.palette.mode).toBe('light');
    expect(theme.palette.primary.main).toBe('#ff0000');
    expect(theme.shape.borderRadius).toBe(30);
    expect(theme.components.MuiCssBaseline.styleOverrides.html.fontSize).toBe('26px');
  });

  it('falls back to the large text and a dark theme', () => {
    const theme = kioskTheme({ ...DEFAULTS, mode: 'neon' }, 'unknown');
    expect(theme.palette.mode).toBe('dark');
    expect(theme.components.MuiCssBaseline.styleOverrides.html.fontSize).toBe('20px');
  });

  it('asks the standard app for the file of a theme', () => {
    expect(themeUrl('night')).toBe('/api/v1/kiosk_standard/themes/night.css');
  });
});
