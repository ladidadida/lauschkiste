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

import RefreshIcon from '@mui/icons-material/Refresh';
import SearchIcon from '@mui/icons-material/Search';

import PubSubContext from '../../context/pubsub/context';
import { refreshLibrary } from '../../utils/library-api';
import { LIBRARY_SCANNED_TOPIC } from '../../config';

// Stop the spinner even if the scan event never arrives
const REFRESH_TIMEOUT_MS = 60000;

const CONTENT_TABS = ['audiobooks', 'radio', 'podcasts'];

const LibraryHeader = ({ handleMusicFilter, musicFilter, showContentTabs = true, sources }) => {
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

  const pathParts = pathname.split('/').filter(Boolean);
  const activeSource = pathParts[1] || 'overview';
  const activeView = pathParts[2];
  const source = sources.find(({ id }) => id === activeSource);
  const contentTabs = showContentTabs ? CONTENT_TABS : [];
  const sourceIds = ['overview', ...sources.map(({ id }) => id), ...contentTabs];
  const sourceValue = sourceIds.includes(activeSource) ? activeSource : false;

  const navigateTo = (path) => {
    localStorage.setItem('libraryLastListView', path);
    navigate(`/library/${path}${urlSearch}`);
  };

  const iconLabel = showSearchInput
    ? t('library.header.search-hide')
    : t('library.header.search-show');

  return (
    <Grid container size={12} sx={{ marginBottom: '8px' }}>
      <Box
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          minWidth: 0,
          width: '100%',
        }}
      >
        <Tabs
          aria-label={t('library.header.sources-label')}
          onChange={(_event, value) => {
            if (contentTabs.includes(value)) {
              navigateTo(value);
              return;
            }
            const nextSource = sources.find(({ id }) => id === value);
            const firstView = nextSource?.views?.[0]?.id;
            navigateTo(
              value === 'overview' || !firstView
                ? 'overview'
                : `${value}/${firstView}`,
            );
          }}
          scrollButtons="auto"
          value={sourceValue}
          variant="scrollable"
          sx={{ flex: 1, minWidth: 0 }}
        >
          <Tab label={t('library.header.overview')} value="overview" />
          {sources.map(({ id, label }) => (
            <Tab
              key={id}
              label={t(`library.sources.${id}`, { defaultValue: label })}
              value={id}
            />
          ))}
          {contentTabs.map((id) => (
            <Tab key={id} label={t(`library.header.${id}`)} value={id} />
          ))}
        </Tabs>
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
      </Box>
      {source?.views?.length > 1 &&
        <Tabs
          aria-label={t('library.header.views-label')}
          onChange={(_event, value) => navigateTo(`${source.id}/${value}`)}
          scrollButtons="auto"
          value={source.views.some(({ id }) => id === activeView) ? activeView : false}
          variant="scrollable"
          sx={{ borderBottom: 1, borderColor: 'divider', width: '100%' }}
        >
          {source.views.map(({ id, label }) => (
            <Tab
              key={id}
              label={t(`library.header.${id}`, { defaultValue: label })}
              value={id}
            />
          ))}
        </Tabs>
      }
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
