import { useCallback, useContext, useEffect, useState } from 'react';
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
  Stack,
  Typography,
} from '@mui/material';

import PodcastsIcon from '@mui/icons-material/Podcasts';

import AppSettingsContext from '../../../context/appsettings/context';
import PubSubContext from '../../../context/pubsub/context';
import request from '../../../utils/request';
import { LIBRARY_SCANNED_TOPIC, PODCASTS_TOPIC } from '../../../config';
import { AudiobookItem, progressOf } from './audiobooks';

const Section = ({ children, title }) => (
  <Box component="section" sx={{ width: '100%' }}>
    <Typography component="h2" sx={{ paddingX: 1 }} variant="h6">{title}</Typography>
    {children}
  </Box>
);

// Audiobooks in progress and podcasts with unheard episodes.
const Continue = ({ musicFilter }) => {
  const { t } = useTranslation();
  const [books, setBooks] = useState([]);
  const [podcasts, setPodcasts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const { settings: { show_covers: showCovers } = {} } = useContext(AppSettingsContext);
  const { state: { [LIBRARY_SCANNED_TOPIC]: lastScan, [PODCASTS_TOPIC]: podcastsChanged } = {} } = useContext(PubSubContext);

  const load = useCallback(async () => {
    const [{ result: bookList }, { result: podcastList }] = await Promise.all([
      request('audiobooksList'),
      request('podcastsList'),
    ]);
    setBooks((bookList || []).filter((book) => !book.finished && progressOf(book) > 0));
    setPodcasts((podcastList || []).filter(({ unheard }) => unheard > 0));
    setIsLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load, lastScan, podcastsChanged]);

  const query = musicFilter.toLowerCase();
  const visibleBooks = books.filter(({ title }) => title.toLowerCase().includes(query));
  const visiblePodcasts = podcasts.filter(({ name }) => name.toLowerCase().includes(query));

  if (isLoading) return <CircularProgress />;
  if (!books.length && !podcasts.length) {
    return (
      <Stack spacing={2} sx={{ padding: 1, width: '100%' }}>
        <Typography>{t('library.continue.empty')}</Typography>
        <Stack direction="row" spacing={1}>
          <Button component={Link} to="/library/music/albums" variant="outlined">
            {t('library.header.music')}
          </Button>
          <Button component={Link} to="/library/audiobooks" variant="outlined">
            {t('library.header.audiobooks')}
          </Button>
        </Stack>
      </Stack>
    );
  }

  return (
    <Stack spacing={2} sx={{ width: '100%' }}>
      {visibleBooks.length > 0 &&
        <Section title={t('library.header.audiobooks')}>
          <List>
            {visibleBooks.map((book) => (
              <AudiobookItem book={book} key={book.book} onChanged={load} showCovers={showCovers} />
            ))}
          </List>
        </Section>
      }
      {visiblePodcasts.length > 0 &&
        <Section title={t('library.continue.new-episodes')}>
          <List>
            {visiblePodcasts.map((podcast) => (
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
                  <ListItemText primary={podcast.name} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Section>
      }
    </Stack>
  );
};

export default Continue;
