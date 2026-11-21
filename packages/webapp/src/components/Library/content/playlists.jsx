import { useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import {
  Avatar,
  Box,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemAvatar,
  ListItemButton,
  ListItemText,
  Typography,
} from '@mui/material';

import AddIcon from '@mui/icons-material/Add';
import QueueMusicIcon from '@mui/icons-material/QueueMusic';

import AppSettingsContext from '../../../context/appsettings/context';
import request from '../../../utils/request';
import { coverSrc, toHHMMSS } from '../../../utils/utils';
import ConfirmDialog from './confirm-dialog';
import FormDialog from './form-dialog';
import ItemMenu from './item-menu';

export const playlistPath = (id) => `/library/music/playlists/${encodeURIComponent(id)}`;

const Playlists = ({ musicFilter }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [playlists, setPlaylists] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const { settings: { show_covers: showCovers } = {} } = useContext(AppSettingsContext);

  const load = useCallback(async () => {
    const { result, error: requestError } = await request('playlistsList');
    setIsLoading(false);
    setError(requestError || null);
    if (result) setPlaylists(result);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const visible = useMemo(() => {
    const query = musicFilter.toLowerCase();
    return playlists.filter(({ title }) => !query || title.toLowerCase().includes(query));
  }, [playlists, musicFilter]);

  const remove = async () => {
    await request('playlistDelete', { playlist: deleting.id });
    setDeleting(null);
    load();
  };

  if (isLoading) return <CircularProgress />;
  if (error) return <Typography>{t('library.loading-error')}</Typography>;

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', paddingX: 1 }}>
        <Button onClick={() => setIsCreating(true)} startIcon={<AddIcon />} sx={{ minHeight: 44 }} variant="outlined">
          {t('library.playlists.new')}
        </Button>
      </Box>
      {!playlists.length && <Typography sx={{ padding: 1 }}>{t('library.playlists.empty')}</Typography>}
      <List sx={{ width: '100%' }}>
        {visible.map((playlist) => (
          <ListItem
            disablePadding
            key={playlist.id}
            secondaryAction={
              <ItemMenu
                items={[
                  { label: t('library.playlists.edit'), onClick: () => navigate(playlistPath(playlist.id)) },
                  { label: t('general.buttons.delete'), onClick: () => setDeleting(playlist) },
                ]}
                label={t('library.playlists.menu', { title: playlist.title })}
              />
            }
          >
            <ListItemButton onClick={() => request('playlist_play', { playlist: playlist.id })}>
              {showCovers &&
                <ListItemAvatar>
                  <Avatar alt="" src={playlist.cover_url ? coverSrc(playlist.cover_url) : undefined} variant="rounded">
                    <QueueMusicIcon />
                  </Avatar>
                </ListItemAvatar>
              }
              <ListItemText
                primary={playlist.title}
                secondary={`${t('library.playlists.tracks', { count: playlist.tracks })}${playlist.duration
                  ? ` · ${toHHMMSS(playlist.duration)}` : ''}`}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <FormDialog
        confirmLabel={t('library.playlists.create')}
        fields={[{ name: 'title', label: t('library.playlists.title-label'), required: true }]}
        onClose={() => setIsCreating(false)}
        onSaved={(created) => {
          setIsCreating(false);
          navigate(playlistPath(created.id));
        }}
        onSubmit={({ title }) => request('playlistCreate', { title, files: [] })}
        open={isCreating}
        title={t('library.playlists.new')}
      />
      <ConfirmDialog
        onClose={() => setDeleting(null)}
        onConfirm={remove}
        open={Boolean(deleting)}
        text={t('library.playlists.delete-text')}
        title={t('library.playlists.delete-title', { title: deleting?.title })}
      />
    </Box>
  );
};

export default Playlists;
