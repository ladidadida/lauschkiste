import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import {
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListSubheader,
  TextField,
  Typography,
} from '@mui/material';

import AlbumIcon from '@mui/icons-material/Album';
import CloseIcon from '@mui/icons-material/Close';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import SearchIcon from '@mui/icons-material/Search';

import request from '../../../utils/request';
import { LOCAL_LIBRARY_SOURCE } from '../../../config';

const MIN_LENGTH = 2;
const DELAY_MS = 300;

// Albums of the found songs, in order of appearance.
const albumsOf = (songs) => {
  const albums = new Map();
  songs.forEach(({ album, albumartist, artist }) => {
    if (!album) return;
    const albumArtist = albumartist || artist || null;
    const key = `${albumArtist}\u0000${album}`;
    if (!albums.has(key)) albums.set(key, { album, albumartist: albumArtist });
  });
  return [...albums.values()];
};

// Search the music library from the player: tap a song or album to play it.
const MusicSearch = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [songs, setSongs] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    const text = query.trim();
    if (text.length < MIN_LENGTH) {
      setSongs([]);
      return undefined;
    }
    let isCurrent = true;
    const timeout = setTimeout(async () => {
      setIsSearching(true);
      const { result } = await request('librarySearch', { query: text });
      if (!isCurrent) return;
      setIsSearching(false);
      setSongs((result || []).filter(({ file }) => file.startsWith('music/')));
    }, DELAY_MS);
    return () => {
      isCurrent = false;
      clearTimeout(timeout);
    };
  }, [query]);

  const albums = useMemo(() => albumsOf(songs), [songs]);

  const close = () => setOpen(false);

  const playAlbum = ({ albumartist, album }) => {
    request('play_album', { albumartist, album, provider: LOCAL_LIBRARY_SOURCE });
    close();
  };

  const openAlbum = ({ albumartist, album }) => {
    close();
    navigate(`/library/${LOCAL_LIBRARY_SOURCE}/albums/${encodeURIComponent(albumartist || '')}/${
      encodeURIComponent(album)}`);
  };

  const playSong = ({ file }) => {
    request('play_single', { song_url: file });
    close();
  };

  return (
    <>
      <IconButton
        aria-label={t('player.search.title')}
        onClick={() => setOpen(true)}
        title={t('player.search.title')}
      >
        <SearchIcon />
      </IconButton>
      <Dialog fullScreen onClose={close} open={open}>
        <DialogTitle sx={{ alignItems: 'center', display: 'flex', gap: 1 }}>
          <TextField
            autoFocus
            fullWidth
            label={t('player.search.label')}
            onChange={(event) => setQuery(event.target.value)}
            size="small"
            value={query}
          />
          <IconButton aria-label={t('general.buttons.close')} onClick={close}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ paddingX: 0 }}>
          {query.trim().length >= MIN_LENGTH && !isSearching && !songs.length &&
            <Typography sx={{ padding: 2 }}>{t('player.search.nothing')}</Typography>
          }
          {albums.length > 0 &&
            <List subheader={<ListSubheader>{t('player.search.albums')}</ListSubheader>}>
              {albums.map((album) => (
                <ListItem
                  disablePadding
                  key={`${album.albumartist}:${album.album}`}
                  secondaryAction={
                    <IconButton
                      aria-label={t('player.display.show-in-library')}
                      edge="end"
                      onClick={() => openAlbum(album)}
                    >
                      <KeyboardArrowRightIcon />
                    </IconButton>
                  }
                >
                  <ListItemButton onClick={() => playAlbum(album)}>
                    <AlbumIcon sx={{ marginRight: 2 }} />
                    <ListItemText primary={album.album} secondary={album.albumartist} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          }
          {songs.length > 0 &&
            <List subheader={<ListSubheader>{t('player.search.songs')}</ListSubheader>}>
              {songs.map((song) => (
                <ListItem disablePadding key={song.file}>
                  <ListItemButton onClick={() => playSong(song)}>
                    <ListItemText
                      primary={song.title || song.file.split('/').pop()}
                      secondary={[song.artist, song.album].filter(Boolean).join(' · ')}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          }
        </DialogContent>
      </Dialog>
    </>
  );
};

export { albumsOf };
export default MusicSearch;
