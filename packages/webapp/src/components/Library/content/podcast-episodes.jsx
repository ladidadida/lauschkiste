import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import {
  Alert,
  Avatar,
  Box,
  Button,
  CircularProgress,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material';

import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PodcastsIcon from '@mui/icons-material/Podcasts';
import RefreshIcon from '@mui/icons-material/Refresh';

import request, { requestErrorMessage } from '../../../utils/request';
import { toHHMMSS } from '../../../utils/utils';
import ConfirmDialog from './confirm-dialog';
import FormDialog from './form-dialog';
import ItemMenu from './item-menu';

const formatDate = (iso, language) => {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString(language, { day: 'numeric', month: 'short', year: 'numeric' });
  }
  catch {
    return '';
  }
};

const PodcastEpisodes = ({ musicFilter }) => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { podcast: podcastId } = useParams();
  const [podcast, setPodcast] = useState(null);
  const [episodes, setEpisodes] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const load = useCallback(async () => {
    const [{ result: podcasts }, { result, error: requestError }] = await Promise.all([
      request('podcastsList'),
      request('podcastEpisodes', { podcast: podcastId }),
    ]);
    setPodcast((podcasts || []).find(({ id }) => id === podcastId) || null);
    setIsLoading(false);
    setError(requestError ? (requestErrorMessage(requestError) || t('library.loading-error')) : null);
    if (result) setEpisodes(result);
  }, [podcastId, t]);

  useEffect(() => {
    load();
  }, [load]);

  const visible = useMemo(() => {
    const query = musicFilter.toLowerCase();
    return query ? episodes.filter(({ title }) => title.toLowerCase().includes(query)) : episodes;
  }, [episodes, musicFilter]);

  const refresh = async () => {
    setIsRefreshing(true);
    const { error: requestError } = await request('refreshPodcasts', { podcast: podcastId });
    setIsRefreshing(false);
    if (requestError) setError(requestErrorMessage(requestError) || t('library.loading-error'));
    else load();
  };

  const setHeard = async (episode, heard) => {
    await request('podcastSetHeard', { podcast: podcastId, episode, heard });
    load();
  };

  const remove = async () => {
    await request('deletePodcast', { podcast: podcastId });
    navigate('/library/podcasts');
  };

  if (isLoading) return <CircularProgress />;

  return (
    <Box sx={{ width: '100%' }}>
      <Stack direction="row" sx={{ alignItems: 'center', gap: 1, paddingX: 1 }}>
        <IconButton
          aria-label={t('header.back')}
          component={Link}
          nativeButton={false}
          to="/library/podcasts"
        >
          <ArrowBackIcon />
        </IconButton>
        <Avatar alt="" src={podcast?.image || undefined} variant="rounded">
          <PodcastsIcon />
        </Avatar>
        <Typography component="h2" noWrap sx={{ flex: 1 }} variant="h6">
          {podcast?.name || podcastId}
        </Typography>
        <IconButton
          aria-label={t('library.podcasts.refresh')}
          disabled={isRefreshing}
          onClick={refresh}
          title={t('library.podcasts.refresh')}
        >
          {isRefreshing ? <CircularProgress size={24} /> : <RefreshIcon />}
        </IconButton>
        <ItemMenu
          items={[
            { label: t('library.podcasts.rename'), onClick: () => setIsRenaming(true) },
            { label: t('library.podcasts.unsubscribe'), onClick: () => setIsDeleting(true) },
          ]}
          label={t('library.podcasts.menu', { name: podcast?.name || podcastId })}
        />
      </Stack>
      {error && <Alert severity="warning" sx={{ margin: 1 }}>{error}</Alert>}
      {episodes.length > 0 &&
        <Box sx={{ paddingX: 1, paddingY: 1 }}>
          <Button
            onClick={() => request('podcast_play', { podcast: podcastId })}
            startIcon={<PlayArrowIcon />}
            variant="contained"
          >
            {t('library.podcasts.play-newest')}
          </Button>
        </Box>
      }
      {!error && !episodes.length && <Typography sx={{ padding: 1 }}>{t('library.podcasts.no-episodes')}</Typography>}
      <List sx={{ width: '100%' }}>
        {visible.map((episode) => {
          const progress = episode.duration && episode.elapsed
            ? Math.min(100, Math.round((episode.elapsed / episode.duration) * 100))
            : 0;
          const details = [
            formatDate(episode.published, i18n.language),
            episode.duration ? toHHMMSS(episode.duration) : null,
            episode.heard ? t('library.podcasts.heard') : null,
          ].filter(Boolean).join(' · ');

          return (
            <ListItem
              disablePadding
              key={episode.id}
              secondaryAction={
                <ItemMenu
                  items={[episode.heard
                    ? { label: t('library.podcasts.mark-unheard'), onClick: () => setHeard(episode.id, false) }
                    : { label: t('library.podcasts.mark-heard'), onClick: () => setHeard(episode.id, true) }]}
                  label={t('library.podcasts.episode-menu', { title: episode.title })}
                />
              }
            >
              <ListItemButton
                onClick={() => request('podcast_play', { podcast: podcastId, episode: episode.id })}
              >
                <ListItemText
                  primary={
                    <Box component="span" sx={{ alignItems: 'center', display: 'flex', gap: 0.5 }}>
                      {episode.title}
                      {episode.heard && <CheckCircleIcon color="success" fontSize="small" />}
                    </Box>
                  }
                  secondary={
                    <Box component="span" sx={{ display: 'block' }}>
                      <Box component="span" sx={{ display: 'block' }}>{details}</Box>
                      {progress > 0 && !episode.heard &&
                        <LinearProgress
                          aria-label={t('library.podcasts.progress-label', { title: episode.title })}
                          component="span"
                          sx={{ display: 'block', marginTop: 0.5 }}
                          value={progress}
                          variant="determinate"
                        />
                      }
                    </Box>
                  }
                  slotProps={{ primary: { sx: { opacity: episode.heard ? 0.7 : 1 } } }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
      <FormDialog
        fields={[{ name: 'name', label: t('library.podcasts.name'), required: true }]}
        initialValues={{ name: podcast?.name || '' }}
        onClose={() => setIsRenaming(false)}
        onSaved={() => {
          setIsRenaming(false);
          load();
        }}
        onSubmit={({ name }) => request('renamePodcast', { podcast: podcastId, name })}
        open={isRenaming}
        title={t('library.podcasts.rename')}
      />
      <ConfirmDialog
        confirmLabel={t('library.podcasts.unsubscribe')}
        onClose={() => setIsDeleting(false)}
        onConfirm={remove}
        open={isDeleting}
        text={t('library.podcasts.unsubscribe-text')}
        title={t('library.podcasts.unsubscribe-title', { name: podcast?.name || podcastId })}
      />
    </Box>
  );
};

export default PodcastEpisodes;
