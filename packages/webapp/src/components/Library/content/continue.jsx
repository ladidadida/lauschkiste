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
import RadioIcon from '@mui/icons-material/Radio';

import AppSettingsContext from '../../../context/appsettings/context';
import PubSubContext from '../../../context/pubsub/context';
import request from '../../../utils/request';
import { LIBRARY_SCANNED_TOPIC, PODCASTS_TOPIC, RADIO_TOPIC } from '../../../config';
import { AudiobookItem, progressOf } from './audiobooks';
import ItemMenu from './item-menu';

const RECENT_STATIONS = 8;

const Section = ({ children, title }) => (
  <Box component="section" sx={{ width: '100%' }}>
    <Typography component="h2" sx={{ paddingX: 1 }} variant="h6">{title}</Typography>
    {children}
  </Box>
);

// Audiobooks in progress, podcasts with unheard episodes and the radio stations played last; each can be taken off.
const Continue = ({ musicFilter }) => {
  const { t } = useTranslation();
  const [books, setBooks] = useState([]);
  const [podcasts, setPodcasts] = useState([]);
  const [stations, setStations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const { settings: { show_covers: showCovers } = {} } = useContext(AppSettingsContext);
  const {
    state: { [LIBRARY_SCANNED_TOPIC]: lastScan, [PODCASTS_TOPIC]: podcastsChanged, [RADIO_TOPIC]: radioChanged } = {},
  } = useContext(PubSubContext);

  const load = useCallback(async () => {
    const [{ result: bookList }, { result: podcastList }, { result: stationList }] = await Promise.all([
      request('audiobooksList'),
      request('podcastsList'),
      request('radioStations'),
    ]);
    setBooks((bookList || []).filter((book) => !book.finished && !book.hidden && progressOf(book) > 0));
    setPodcasts((podcastList || []).filter(({ unheard, hidden }) => unheard > 0 && !hidden));
    setStations((stationList || [])
      .filter(({ last_played: lastPlayed }) => lastPlayed)
      .sort((a, b) => b.last_played.localeCompare(a.last_played))
      .slice(0, RECENT_STATIONS));
    setIsLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load, lastScan, podcastsChanged, radioChanged]);

  const query = musicFilter.toLowerCase();
  const visibleBooks = books.filter(({ title }) => title.toLowerCase().includes(query));
  const visiblePodcasts = podcasts.filter(({ name }) => name.toLowerCase().includes(query));
  const visibleStations = stations.filter(({ name }) => name.toLowerCase().includes(query));

  const take = (command, args) => async () => {
    await request(command, args);
    load();
  };

  if (isLoading) return <CircularProgress />;
  if (!books.length && !podcasts.length && !stations.length) {
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
              <AudiobookItem
                book={book}
                key={`${book.source}/${book.book}`}
                onChanged={load}
                onHide={take('audiobookHide', { book: book.book, source: book.source })}
                showCovers={showCovers}
              />
            ))}
          </List>
        </Section>
      }
      {visiblePodcasts.length > 0 &&
        <Section title={t('library.continue.new-episodes')}>
          <List>
            {visiblePodcasts.map((podcast) => (
              <ListItem
                disablePadding
                key={podcast.id}
                secondaryAction={
                  <ItemMenu
                    items={[{ label: t('library.continue.remove'), onClick: take('podcastHide', { podcast: podcast.id }) }]}
                    label={t('library.podcasts.menu', { name: podcast.name })}
                  />
                }
              >
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
      {visibleStations.length > 0 &&
        <Section title={t('library.continue.radio')}>
          <List>
            {visibleStations.map((station) => (
              <ListItem
                disablePadding
                key={station.id}
                secondaryAction={
                  <ItemMenu
                    items={[{
                      label: t('library.continue.remove'),
                      onClick: take('forgetRadioRecent', { station: station.id }),
                    }]}
                    label={t('library.radio.menu', { name: station.name })}
                  />
                }
              >
                <ListItemButton onClick={() => request('radio_play', { station: station.id })}>
                  <ListItemAvatar>
                    <Avatar alt="" src={station.logo || undefined} variant="rounded">
                      <RadioIcon />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText primary={station.name} />
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
