import { useContext, useEffect, useRef, useState } from "react";
import {
  useLocation,
  useNavigate,
} from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import {
  Box,
  CircularProgress,
  Grid,
  IconButton,
  Tab,
  Tabs,
  TextField,
} from "@mui/material";

import HistoryIcon from '@mui/icons-material/History';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import MusicNoteIcon from '@mui/icons-material/MusicNote';
import PodcastsIcon from '@mui/icons-material/Podcasts';
import RadioIcon from '@mui/icons-material/Radio';
import RefreshIcon from '@mui/icons-material/Refresh';
import SearchIcon from '@mui/icons-material/Search';

import PubSubContext from '../../context/pubsub/context';
import { refreshLibrary } from '../../utils/library-api';
import { LIBRARY_SCANNED_TOPIC } from '../../config';

// Stop the spinner even if the scan event never arrives
const REFRESH_TIMEOUT_MS = 60000;

const TABS = ['continue', 'music', 'audiobooks', 'radio', 'podcasts'];
const TAB_ICONS = {
  continue: HistoryIcon,
  music: MusicNoteIcon,
  audiobooks: MenuBookIcon,
  radio: RadioIcon,
  podcasts: PodcastsIcon,
};
const TAB_PATHS = {
  continue: 'continue',
  music: 'music/albums',
  audiobooks: 'audiobooks',
  radio: 'radio',
  podcasts: 'podcasts',
};
const VIEWS = {
  music: [['albums', 'music/albums'], ['folders', 'music/folders']],
  audiobooks: [['books', 'audiobooks'], ['folders', 'audiobooks/folders']],
};

// The tab and view of a library path; album pages (`/library/<source>/albums/...`) belong to music.
export const activeTabAndView = (pathname) => {
  const [, tab, view] = pathname.split('/').filter(Boolean);
  if (TABS.includes(tab)) {
    if (tab === 'music') return ['music', view === 'folders' ? 'folders' : 'albums'];
    if (tab === 'audiobooks') return ['audiobooks', view === 'folders' ? 'folders' : 'books'];
    return [tab, undefined];
  }
  return view === 'albums' ? ['music', 'albums'] : [false, undefined];
};

const LibraryHeader = ({ handleMusicFilter, isSelecting = false, musicFilter }) => {
  const { pathname, search: urlSearch } = useLocation();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [showSearchInput, setShowSearchInput] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const { state: { [LIBRARY_SCANNED_TOPIC]: lastScan } = {} } = useContext(PubSubContext);
  const refreshTimeout = useRef(null);

  useEffect(() => {
    setIsRefreshing(false);
    clearTimeout(refreshTimeout.current);
  }, [lastScan]);

  useEffect(() => () => clearTimeout(refreshTimeout.current), []);

  const refresh = async () => {
    setIsRefreshing(true);
    refreshTimeout.current = setTimeout(() => setIsRefreshing(false), REFRESH_TIMEOUT_MS);
    try {
      await refreshLibrary();
    } catch {
      setIsRefreshing(false);
      clearTimeout(refreshTimeout.current);
    }
  };

  const tabs = isSelecting ? ['music'] : TABS;
  const [activeTab, activeView] = activeTabAndView(pathname);
  const views = VIEWS[activeTab];

  const navigateTo = (path) => {
    localStorage.setItem('libraryLastListView', path);
    navigate(`/library/${path}${urlSearch}`);
  };

  const iconLabel = showSearchInput
    ? t('library.header.search-hide')
    : t('library.header.search-show');

  const buttons = (
    <>
      <IconButton
        aria-label={t('library.header.refresh')}
        disabled={isRefreshing}
        onClick={refresh}
        title={t('library.header.refresh')}
      >
        {isRefreshing ? <CircularProgress size={24} /> : <RefreshIcon />}
      </IconButton>
      <IconButton
        aria-label={iconLabel}
        color={showSearchInput ? 'primary' : undefined}
        onClick={() => setShowSearchInput(!showSearchInput)}
        title={iconLabel}
      >
        <SearchIcon />
      </IconButton>
    </>
  );

  return (
    <Grid container size={12} sx={{ marginBottom: '8px' }}>
      <Tabs
        aria-label={t('library.header.sections-label')}
        onChange={(_event, value) => navigateTo(TAB_PATHS[value])}
        value={tabs.includes(activeTab) ? activeTab : false}
        variant="fullWidth"
        sx={{ borderBottom: 1, borderColor: 'divider', width: '100%' }}
      >
        {tabs.map((id) => {
          const Icon = TAB_ICONS[id];
          return (
            <Tab
              icon={<Icon />}
              key={id}
              label={t(`library.header.${id}`)}
              sx={{ fontSize: '0.7rem', minHeight: 56, minWidth: 0, paddingX: 0.5, textTransform: 'none' }}
              value={id}
            />
          );
        })}
      </Tabs>
      <Box sx={{ alignItems: 'center', borderBottom: 1, borderColor: 'divider', display: 'flex', width: '100%' }}>
        {views
          ? (
            <Tabs
              aria-label={t('library.header.views-label')}
              onChange={(_event, value) => navigateTo(views.find(([id]) => id === value)[1])}
              value={activeView}
              variant="fullWidth"
              sx={{ flex: 1, minWidth: 0 }}
            >
              {views.map(([id]) => (
                <Tab key={id} label={t(`library.header.${id}`)} value={id} />
              ))}
            </Tabs>
          )
          : <Box sx={{ flex: 1 }} />
        }
        {buttons}
      </Box>
      {showSearchInput &&
        <TextField
          autoFocus
          focused
          fullWidth
          id="library-search"
          label={t('library.header.search-label')}
          onChange={handleMusicFilter}
          size="small"
          sx={{ marginTop: 1 }}
          value={musicFilter}
          variant="outlined"
        />
      }
    </Grid>
  );
}

export default LibraryHeader;
