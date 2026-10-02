import { useEffect, useState } from "react";
import {
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router-dom';

import {
  CircularProgress,
  Grid,
} from '@mui/material';

import Albums from './albums';
import LibraryOverview from './overview';
import SongList from './albums/song-list';
import Folders from './folders';
import Audiobooks from '../content/audiobooks';
import PodcastEpisodes from '../content/podcast-episodes';
import Podcasts from '../content/podcasts';
import Radio from '../content/radio';
import LibraryHeader from "../library-header";
import SelectorHeader from "../selector-header";

import { buildActionData } from '../../Cards/utils';
import request from '../../../utils/request';
import { LOCAL_LIBRARY_SOURCE } from '../../../config';

const LOCAL_SOURCE = {
  id: LOCAL_LIBRARY_SOURCE,
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
};

const RedirectWithSearch = ({ to }) => {
  const [searchParams] = useSearchParams();
  const search = searchParams.toString();
  return <Navigate to={`${to}${search ? `?${search}` : ''}`} replace />;
};

const findSourceView = (sources, provider, view) => (
  sources
    .find(({ id }) => id === provider)
    ?.views?.find(({ id }) => id === view)
);

const LibrarySourceView = ({
  isSelecting,
  isLoadingSources,
  musicFilter,
  sources,
}) => {
  const { provider, view } = useParams();
  const sourceView = findSourceView(sources, provider, view);

  if (!sourceView && isLoadingSources) return <CircularProgress />;
  if (!sourceView) return <RedirectWithSearch to="/library/overview" />;
  if (sourceView.kind === 'folders') {
    return (
      <RedirectWithSearch
        to={`/library/${provider}/${view}/.%2F`}
      />
    );
  }

  return (
    <Albums
      contentTypes={sourceView.content_types}
      isSelecting={isSelecting}
      musicFilter={musicFilter}
      provider={provider}
      view={view}
    />
  );
};

const LibraryFolderView = ({
  isLoadingSources,
  isSelecting,
  musicFilter,
  registerMusicToCard,
  sources,
}) => {
  const { provider, view } = useParams();
  const sourceView = findSourceView(sources, provider, view);

  if (!sourceView && isLoadingSources) return <CircularProgress />;
  if (sourceView?.kind !== 'folders') {
    return <RedirectWithSearch to="/library/overview" />;
  }

  return (
    <Folders
      musicFilter={musicFilter}
      isSelecting={isSelecting}
      registerMusicToCard={registerMusicToCard}
    />
  );
};

const LibraryItemView = ({
  isLoadingSources,
  isSelecting,
  registerMusicToCard,
  sources,
}) => {
  const { provider, view } = useParams();
  const sourceView = findSourceView(sources, provider, view);

  if (!sourceView && isLoadingSources) return <CircularProgress />;
  if (!sourceView || sourceView.kind === 'folders') {
    return <RedirectWithSearch to="/library/overview" />;
  }

  return (
    <SongList
      isSelecting={isSelecting}
      provider={provider}
      registerMusicToCard={registerMusicToCard}
      view={view}
    />
  );
};

const LegacyAlbumRedirect = () => {
  const { artist, album } = useParams();
  return (
    <RedirectWithSearch
      to={`/library/${LOCAL_LIBRARY_SOURCE}/albums/${encodeURIComponent(artist)}/${encodeURIComponent(album)}`}
    />
  );
};

const LegacyFolderRedirect = () => {
  const { dir } = useParams();
  return (
    <RedirectWithSearch
      to={`/library/${LOCAL_LIBRARY_SOURCE}/folders/${encodeURIComponent(dir)}`}
    />
  );
};

const LibraryLists = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isSelecting] = useState(searchParams.get('isSelecting'));
  const [cardId] = useState(searchParams.get('cardId'));
  const [musicFilter, setMusicFilter] = useState('');
  const [sources, setSources] = useState([LOCAL_SOURCE]);
  const [isLoadingSources, setIsLoadingSources] = useState(true);

  useEffect(() => {
    let isCurrent = true;
    const fetchSources = async () => {
      const { result } = await request('librarySources');
      if (!isCurrent) return;
      if (result?.length) setSources(result);
      setIsLoadingSources(false);
    };
    fetchSources();
    return () => {
      isCurrent = false;
    };
  }, []);

  const handleMusicFilter = (event) => {
    setMusicFilter(event.target.value);
  };

  const registerMusicToCard = (command, args) => {
    const actionData = buildActionData('play_music', command, args);
    const state = {
      registerCard: {
        actionData,
        cardId,
      },
    };

    navigate('/cards/register', { state });
  };

  return (
    <Grid container id="library">
      {isSelecting && <SelectorHeader />}
      <Grid container size={12} sx={{ padding: '10px' }}>
        <LibraryHeader
          handleMusicFilter={handleMusicFilter}
          musicFilter={musicFilter}
          showContentTabs={!isSelecting}
          sources={sources}
        />
        <Grid
          container
          size={12}
          spacing={1}
          sx={{
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <Routes>
            <Route
              path="overview"
              element={
                <LibraryOverview
                  musicFilter={musicFilter}
                  sources={sources}
                />
              }
              exact
            />
            <Route path="audiobooks" element={<Audiobooks musicFilter={musicFilter} />} />
            <Route path="radio" element={<Radio musicFilter={musicFilter} />} />
            <Route path="podcasts" element={<Podcasts musicFilter={musicFilter} />} />
            <Route path="podcasts/:podcast" element={<PodcastEpisodes musicFilter={musicFilter} />} />
            <Route
              path=":provider/:view"
              element={
                <LibrarySourceView
                  isSelecting={isSelecting}
                  isLoadingSources={isLoadingSources}
                  musicFilter={musicFilter}
                  sources={sources}
                />
              }
              exact
            />
            <Route
              path=":provider/:view/:dir"
              element={
                <LibraryFolderView
                  isLoadingSources={isLoadingSources}
                  isSelecting={isSelecting}
                  musicFilter={musicFilter}
                  registerMusicToCard={registerMusicToCard}
                  sources={sources}
                />
              }
            />
            <Route
              path=":provider/:view/:artist/:album"
              element={
                <LibraryItemView
                  isLoadingSources={isLoadingSources}
                  isSelecting={isSelecting}
                  registerMusicToCard={registerMusicToCard}
                  sources={sources}
                />
              }
            />
            <Route
              path="albums"
              element={<RedirectWithSearch to={`/library/${LOCAL_LIBRARY_SOURCE}/albums`} />}
            />
            <Route
              path="albums/:artist/:album"
              element={<LegacyAlbumRedirect />}
            />
            <Route
              path="folders"
              element={<RedirectWithSearch to={`/library/${LOCAL_LIBRARY_SOURCE}/folders/.%2F`} />}
            />
            <Route
              path="folders/:dir"
              element={<LegacyFolderRedirect />}
            />
            <Route
              path="*"
              element={<RedirectWithSearch to="/library/overview" />}
            />
          </Routes>
        </Grid>
      </Grid>
    </Grid>
  );
};

export default LibraryLists;
