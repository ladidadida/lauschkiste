import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  List,
  ListItemButton,
  ListItemText,
  Stack,
  TextField,
} from '@mui/material';

import request, { requestErrorMessage } from '../../../utils/request';

// Adds `files` to an existing playlist or to a new one.
const AddToPlaylist = ({ files, onClose, open }) => {
  const { t } = useTranslation();
  const [playlists, setPlaylists] = useState([]);
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState(null);

  useEffect(() => {
    if (!open) return;
    setTitle('');
    setMessage(null);
    request('playlistsList').then(({ result }) => setPlaylists(result || []));
  }, [open]);

  const done = ({ result, error }, name) => {
    if (error) {
      setMessage({ severity: 'error', text: requestErrorMessage(error) || t('library.content.save-error') });
      return;
    }
    setMessage({ severity: 'success', text: t('library.playlists.added', { count: files.length, title: name }) });
    request('playlistsList').then(({ result: list }) => setPlaylists(list || []));
    return result;
  };

  const add = async (playlist) => done(await request('playlistAdd', { playlist: playlist.id, files }), playlist.title);

  const create = async (event) => {
    event.preventDefault();
    const name = title.trim();
    if (!name) return;
    if (done(await request('playlistCreate', { title: name, files }), name)) setTitle('');
  };

  return (
    <Dialog fullWidth maxWidth="xs" onClose={onClose} open={open}>
      <DialogTitle>{t('library.playlists.add-to', { count: files.length })}</DialogTitle>
      <DialogContent>
        {message && <Alert severity={message.severity} sx={{ marginBottom: 1 }}>{message.text}</Alert>}
        <List dense>
          {playlists.map((playlist) => (
            <ListItemButton key={playlist.id} onClick={() => add(playlist)}>
              <ListItemText
                primary={playlist.title}
                secondary={t('library.playlists.tracks', { count: playlist.tracks })}
              />
            </ListItemButton>
          ))}
        </List>
        <form onSubmit={create}>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
            <TextField
              fullWidth
              label={t('library.playlists.new-title')}
              onChange={(event) => setTitle(event.target.value)}
              size="small"
              value={title}
            />
            <Button disabled={!title.trim()} type="submit" variant="outlined">{t('library.playlists.create')}</Button>
          </Stack>
        </form>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} sx={{ minHeight: 44 }}>{t('general.buttons.close')}</Button>
      </DialogActions>
    </Dialog>
  );
};

export default AddToPlaylist;
