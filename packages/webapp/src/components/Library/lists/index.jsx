import { useEffect, useState } from "react";
import {
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router-dom';

import { Grid } from '@mui/material';

import Albums from './albums';
import SongList from './albums/song-list';
import Folders from './folders';
import Audiobooks from '../content/audiobooks';
import Continue from '../content/continue';
import PodcastEpisodes from '../content/podcast-episodes';
import Podcasts from '../content/podcasts';
import Radio from '../content/radio';
import LibraryHeader from "../library-header";
import SelectorHeader from "../selector-header";

import { buildActionData } from '../../Cards/utils';
import request from '../../../utils/request';
import { LOCAL_LIBRARY_SOURCE } from '../../../config';

const LOCAL_SOURCE = { id: LOCAL_LIBRARY_SOURCE, label: 'Local' };

const RedirectWithSearch = ({ to }) => {
  const [searchParams] = useSearchParams();
  const search = searchParams.toString();
  return <Navigate to={`${to}${search ? `?${search}` : ''}`} replace />;
};

const FolderView = ({ root, ...props }) => {
  const { dir } = useParams();
  const folder = decodeURIComponent(dir || root);
  if (folder !== root && !folder.startsWith(`${root}/`)) {
    return <RedirectWithSearch to={`/library/${root}/folders/${encodeURIComponent(root)}`} />;
  }
  return <Folders root={root} {...props} />;
};

const LibraryLists = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isSelecting] = useState(searchParams.get('isSelecting'));
  const [cardId] = useState(searchParams.get('cardId'));
  const [musicFilter, setMusicFilter] = useState('');
  const [sources, setSources] = useState([LOCAL_SOURCE]);

  useEffect(() => {
    let isCurrent = true;
    request('librarySources').then(({ result }) => {
      if (isCurrent && result?.length) setSources(result);
    });
    return () => {
      isCurrent = false;
    };
  }, []);

  const handleMusicFilter = (event) => {
    setMusicFilter(event.target.value);
  };

  const registerMusicToCard = (command, args) => {
    const actionData = buildActionData('play_music', command, args);
    navigate('/cards/register', { state: { registerCard: { actionData, cardId } } });
  };

  const folderProps = { isSelecting, musicFilter, registerMusicToCard };

  return (
    <Grid container id="library">
      {isSelecting && <SelectorHeader />}
      <Grid container size={12} sx={{ padding: '10px' }}>
        <LibraryHeader
          handleMusicFilter={handleMusicFilter}
          isSelecting={Boolean(isSelecting)}
          musicFilter={musicFilter}
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
            <Route path="continue" element={<Continue musicFilter={musicFilter} />} />
            <Route path="music" element={<RedirectWithSearch to="/library/music/albums" />} />
            <Route
              path="music/albums"
              element={<Albums musicFilter={musicFilter} sources={sources} />}
            />
            <Route
              path="music/folders"
              element={<RedirectWithSearch to="/library/music/folders/music" />}
            />
            <Route path="music/folders/:dir" element={<FolderView root="music" {...folderProps} />} />
            <Route path="audiobooks" element={<Audiobooks musicFilter={musicFilter} />} />
            <Route
              path="audiobooks/folders"
              element={<RedirectWithSearch to="/library/audiobooks/folders/audiobooks" />}
            />
            <Route
              path="audiobooks/folders/:dir"
              element={<FolderView root="audiobooks" {...folderProps} />}
            />
            <Route path="radio" element={<Radio musicFilter={musicFilter} />} />
            <Route path="podcasts" element={<Podcasts musicFilter={musicFilter} />} />
            <Route path="podcasts/:podcast" element={<PodcastEpisodes musicFilter={musicFilter} />} />
            <Route
              path=":provider/albums/:artist/:album"
              element={<SongList isSelecting={isSelecting} registerMusicToCard={registerMusicToCard} />}
            />
            <Route path="*" element={<RedirectWithSearch to="/library/music/albums" />} />
          </Routes>
        </Grid>
      </Grid>
    </Grid>
  );
};

export default LibraryLists;
