import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { BottomNavigation, BottomNavigationAction, Box, CssBaseline } from '@mui/material';
import { ThemeProvider } from '@mui/material/styles';

import { startPage, visiblePages } from './pages-list';
import PlayerPage from './pages/player';
import {
  AudiobooksShelf, ContinueShelf, Episodes, MusicShelf, PodcastsShelf, RadioShelf,
} from './pages/shelves';
import { OWN_APP, useKioskSettings, useKioskState } from './settings';
import { DEFAULTS, kioskTheme, readVariables, themeUrl } from './theme';

const IDLE_MS = 120_000;
// The core serves the app here; elsewhere (a development server) it must not leave on its own.
const SERVED_PATH = '/kiosk/';

// Loads the CSS file of the theme and reads its variables; until then the defaults apply.
const useThemeVariables = (name) => {
  const [variables, setVariables] = useState(DEFAULTS);
  useEffect(() => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = themeUrl(name);
    link.onload = () => setVariables(readVariables());
    document.head.append(link);
    return () => link.remove();
  }, [name]);
  return variables;
};

// Follows the kiosk module: back to the normal web app when the kiosk is switched off, a new page for another app.
const useKioskGuard = () => {
  const kiosk = useKioskState();
  useEffect(() => {
    if (!kiosk || window.location.pathname !== SERVED_PATH) return;
    if (!kiosk.enabled) window.location.replace('/?kiosk');
    else if (kiosk.app && kiosk.app !== OWN_APP) window.location.reload();
  }, [kiosk]);
};

// Back to the start page after a while without a touch.
const useIdleReset = (reset) => {
  useEffect(() => {
    let timer = setTimeout(reset, IDLE_MS);
    const touched = () => {
      clearTimeout(timer);
      timer = setTimeout(reset, IDLE_MS);
    };
    document.addEventListener('pointerdown', touched);
    return () => {
      clearTimeout(timer);
      document.removeEventListener('pointerdown', touched);
    };
  }, [reset]);
};

const Shell = ({ settings }) => {
  const { t } = useTranslation();
  const [chosen, setChosen] = useState(null);
  const [podcast, setPodcast] = useState(null);
  const pages = useMemo(() => visiblePages(settings), [settings]);
  const page = pages.some(({ id }) => id === chosen) ? chosen : startPage(settings);

  const reset = useCallback(() => {
    setChosen(null);
    setPodcast(null);
  }, []);
  useIdleReset(reset);

  const play = () => {
    setChosen('player');
    setPodcast(null);
  };

  const content = () => {
    if (podcast) return <Episodes onBack={() => setPodcast(null)} onPlay={play} podcast={podcast} />;
    switch (page) {
      case 'continue': return <ContinueShelf onOpen={setPodcast} onPlay={play} />;
      case 'music': return <MusicShelf onPlay={play} />;
      case 'audiobooks': return <AudiobooksShelf onPlay={play} />;
      case 'radio': return <RadioShelf onPlay={play} />;
      case 'podcasts': return <PodcastsShelf onOpen={setPodcast} />;
      default: return <PlayerPage showVolume={settings.show_volume} />;
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Box component="main" sx={{ flex: 1, minHeight: 0, overflowY: 'auto', touchAction: 'pan-y' }}>
        {content()}
      </Box>
      <BottomNavigation
        onChange={(_event, id) => {
          setChosen(id);
          setPodcast(null);
        }}
        showLabels
        sx={{ flex: '0 0 auto', height: '4.5rem' }}
        value={page}
      >
        {pages.map(({ Icon, id, label }) => (
          <BottomNavigationAction icon={<Icon fontSize="large" />} key={id} label={t(label)} sx={{ minWidth: 0 }}
            value={id} />
        ))}
      </BottomNavigation>
    </Box>
  );
};

const KioskApp = () => {
  const settings = useKioskSettings();
  const variables = useThemeVariables(settings.theme);
  const theme = useMemo(() => kioskTheme(variables, settings.text_size), [variables, settings.text_size]);
  useKioskGuard();

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Shell settings={settings} />
    </ThemeProvider>
  );
};

export default KioskApp;
