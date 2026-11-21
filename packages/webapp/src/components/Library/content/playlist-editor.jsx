import { useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Stack,
  TextField,
  Typography,
} from '@mui/material';

import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

import request, { requestErrorMessage } from '../../../utils/request';
import { toHHMMSS } from '../../../utils/utils';
import { moveItem } from './audiobook-editor';

const SEARCH_DELAY_MS = 300;

const describe = ({ artist, album, duration }) => [artist, album, duration ? toHHMMSS(duration) : null]
  .filter(Boolean).join(' · ') || null;

// Title and songs of a playlist; changes are kept until "save".
const PlaylistEditor = () => {
  const { t } = useTranslation();
  const { playlist: encoded } = useParams();
  const playlist = decodeURIComponent(encoded);
  const [title, setTitle] = useState('');
  const [entries, setEntries] = useState(null);
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState([]);
  const [error, setError] = useState('');
  const [loadFailed, setLoadFailed] = useState(false);
  const [saved, setSaved] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    request('playlistGet', { playlist }).then(({ result, error: requestError }) => {
      if (requestError) {
        setError(requestErrorMessage(requestError) || '');
        setLoadFailed(true);
        return;
      }
      setTitle(result.title);
      setEntries(result.entries);
    });
  }, [playlist]);

  useEffect(() => {
    if (query.trim().length < 2) {
      setHits([]);
      return undefined;
    }
    const timer = setTimeout(async () => {
      const { result } = await request('librarySearch', { query: query.trim() });
      setHits((result || []).slice(0, 50));
    }, SEARCH_DELAY_MS);
    return () => clearTimeout(timer);
  }, [query]);

  const change = (next) => {
    setEntries(next);
    setSaved(false);
  };

  const save = async () => {
    setIsSaving(true);
    setError('');
    const { result, error: requestError } = await request('playlistSave', {
      playlist, title: title.trim(), files: entries.map(({ file }) => file),
    });
    setIsSaving(false);
    if (requestError) {
      setError(requestErrorMessage(requestError) || t('library.content.save-error'));
      return;
    }
    setEntries(result.entries);
    setSaved(true);
  };

  if (!entries) {
    return loadFailed
      ? <Alert severity="error">{error || t('library.loading-error')}</Alert>
      : <CircularProgress />;
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', marginBottom: 1 }}>
        <IconButton aria-label={t('library.playlists.back')} component={RouterLink} to="/library/music/playlists">
          <ArrowBackIcon />
        </IconButton>
        <TextField
          fullWidth
          label={t('library.playlists.title-label')}
          onChange={(event) => {
            setTitle(event.target.value);
            setSaved(false);
          }}
          size="small"
          value={title}
        />
      </Stack>
      {error && <Alert severity="error" sx={{ marginBottom: 1 }}>{error}</Alert>}
      <Stack direction="row" spacing={1} sx={{ justifyContent: 'flex-end' }}>
        <Button
          disabled={!saved || !entries.length}
          onClick={() => request('playlist_play', { playlist })}
          startIcon={<PlayArrowIcon />}
          sx={{ minHeight: 44 }}
        >
          {t('library.playlists.play')}
        </Button>
        <Button
          disabled={saved || isSaving || !title.trim()}
          onClick={save}
          sx={{ minHeight: 44 }}
          variant="contained"
        >
          {saved ? t('library.playlists.saved') : t('general.buttons.save')}
        </Button>
      </Stack>
      {!entries.length && <Typography sx={{ padding: 1 }}>{t('library.playlists.no-songs')}</Typography>}
      <List dense>
        {entries.map((entry, index) => (
          <ListItem
            disableGutters
            key={`${index}-${entry.file}`}
            secondaryAction={
              <>
                <IconButton
                  aria-label={t('library.playlists.move-up', { title: entry.title })}
                  disabled={index === 0}
                  onClick={() => change(moveItem(entries, index, -1))}
                >
                  <ArrowUpwardIcon />
                </IconButton>
                <IconButton
                  aria-label={t('library.playlists.move-down', { title: entry.title })}
                  disabled={index === entries.length - 1}
                  onClick={() => change(moveItem(entries, index, 1))}
                >
                  <ArrowDownwardIcon />
                </IconButton>
                <IconButton
                  aria-label={t('library.playlists.remove', { title: entry.title })}
                  edge="end"
                  onClick={() => change(entries.filter((_entry, position) => position !== index))}
                >
                  <DeleteIcon />
                </IconButton>
              </>
            }
            sx={{ paddingRight: 18 }}
          >
            <ListItemText
              primary={`${index + 1}. ${entry.title}`}
              secondary={entry.missing ? t('library.playlists.missing') : describe(entry)}
              sx={entry.missing ? { color: 'text.disabled' } : undefined}
            />
          </ListItem>
        ))}
      </List>
      <Divider sx={{ marginY: 1 }} />
      <TextField
        fullWidth
        helperText={t('library.playlists.search-help')}
        label={t('library.playlists.search-label')}
        onChange={(event) => setQuery(event.target.value)}
        size="small"
        value={query}
      />
      <List dense>
        {hits.map((song) => (
          <ListItem
            disableGutters
            key={song.file}
            secondaryAction={
              <IconButton
                aria-label={t('library.playlists.add-song', { title: song.title || song.file })}
                edge="end"
                onClick={() => change([...entries, {
                  file: song.file, title: song.title || song.file, artist: song.artist, album: song.album,
                  duration: song.duration, missing: false,
                }])}
              >
                <AddIcon />
              </IconButton>
            }
          >
            <ListItemText primary={song.title || song.file} secondary={describe(song)} />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

export default PlaylistEditor;
