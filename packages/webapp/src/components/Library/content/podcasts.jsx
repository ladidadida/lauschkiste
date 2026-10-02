import { useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import {
  Avatar,
  Badge,
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
import PodcastsIcon from '@mui/icons-material/Podcasts';

import PubSubContext from '../../../context/pubsub/context';
import request from '../../../utils/request';
import { PODCASTS_TOPIC } from '../../../config';
import FormDialog from './form-dialog';

const Podcasts = ({ musicFilter }) => {
  const { t } = useTranslation();
  const [podcasts, setPodcasts] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const { state: { [PODCASTS_TOPIC]: changed } = {} } = useContext(PubSubContext);

  const load = useCallback(async () => {
    const { result, error: requestError } = await request('podcastsList');
    setIsLoading(false);
    setError(requestError || null);
    if (result) setPodcasts(result);
  }, []);

  useEffect(() => {
    if (changed?.podcasts) {
      setPodcasts(changed.podcasts);
      setIsLoading(false);
    }
    else {
      load();
    }
  }, [changed, load]);

  const visible = useMemo(() => {
    const query = musicFilter.toLowerCase();
    return query ? podcasts.filter(({ name }) => name.toLowerCase().includes(query)) : podcasts;
  }, [podcasts, musicFilter]);

  if (isLoading) return <CircularProgress />;
  if (error) return <Typography>{t('library.loading-error')}</Typography>;

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', paddingX: 1 }}>
        <Button onClick={() => setIsAdding(true)} startIcon={<AddIcon />}>
          {t('library.podcasts.add')}
        </Button>
      </Box>
      {!podcasts.length && <Typography sx={{ padding: 1 }}>{t('library.podcasts.empty')}</Typography>}
      {podcasts.length > 0 && !visible.length && <Typography>{t('library.albums.no-music')}</Typography>}
      <List sx={{ width: '100%' }}>
        {visible.map((podcast) => (
          <ListItem disablePadding key={podcast.id}>
            <ListItemButton
              component={Link}
              nativeButton={false}
              to={`/library/podcasts/${encodeURIComponent(podcast.id)}`}
            >
              <ListItemAvatar>
                <Badge
                  anchorOrigin={{ horizontal: 'left', vertical: 'top' }}
                  badgeContent={podcast.unheard}
                  color="primary"
                  max={99}
                >
                  <Avatar alt="" src={podcast.image || undefined} variant="rounded">
                    <PodcastsIcon />
                  </Avatar>
                </Badge>
              </ListItemAvatar>
              <ListItemText
                primary={podcast.name}
                secondary={t('library.podcasts.episodes', {
                  count: podcast.episodes,
                  unheard: podcast.unheard,
                })}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <FormDialog
        confirmLabel={t('library.podcasts.subscribe')}
        fields={[
          { name: 'url', label: t('library.podcasts.url'), required: true, type: 'url',
            helperText: t('library.podcasts.url-help') },
          { name: 'name', label: t('library.podcasts.name'), helperText: t('library.podcasts.name-help') },
        ]}
        onClose={() => setIsAdding(false)}
        onSaved={() => {
          setIsAdding(false);
          load();
        }}
        onSubmit={({ url, name }) => request('addPodcast', { url, name: name || undefined })}
        open={isAdding}
        title={t('library.podcasts.add')}
      />
    </Box>
  );
};

export default Podcasts;
