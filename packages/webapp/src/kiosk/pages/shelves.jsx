import { useCallback, useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AutoStoriesIcon from '@mui/icons-material/AutoStories';
import LibraryMusicIcon from '@mui/icons-material/LibraryMusic';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PodcastsIcon from '@mui/icons-material/Podcasts';
import RadioIcon from '@mui/icons-material/Radio';
import {
  Box,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material';

import PubSubContext from '../../context/pubsub/context';
import request from '../../utils/request';
import { coverSrc, flatByAlbum, toHHMMSS } from '../../utils/utils';
import { LIBRARY_SCANNED_TOPIC, PODCASTS_TOPIC, RADIO_TOPIC } from '../../config';
import { Tile, TileGrid } from '../tile';

const progressOf = ({ duration, finished, listened }) => {
  if (finished) return 100;
  return duration ? Math.min(100, Math.round((listened / duration) * 100)) : 0;
};

// Books of other sources (not the local library) name their source in every request.
const sourceArg = (book) => (book.source && book.source !== 'local' ? { source: book.source } : {});

// Loads a list when the page opens and again when `topics` (published events) change.
const useShelf = (load, topics = []) => {
  const [items, setItems] = useState(null);
  const { state } = useContext(PubSubContext);
  const marker = JSON.stringify(topics.map((topic) => state[topic]));
  useEffect(() => {
    let current = true;
    load().then((list) => current && setItems(list));
    return () => {
      current = false;
    };
  }, [load, marker]);
  return items;
};

const Shelf = ({ children, items }) => {
  const { t } = useTranslation();
  if (items === null) return <Box sx={{ display: 'flex', justifyContent: 'center', padding: 4 }}><CircularProgress /></Box>;
  if (!items.length) return <Typography color="text.secondary" sx={{ padding: 3 }}>{t('kiosk.empty')}</Typography>;
  return <TileGrid>{children}</TileGrid>;
};

const albumCover = ({ album, albumartist, content_uri: contentUri, provider }) => async () => {
  const { result } = await request('getAlbumCoverArt', { album, albumartist, content_uri: contentUri, provider });
  const url = result?.cover_url;
  return url && url !== 'CACHE_PENDING' ? coverSrc(url) : null;
};

const loadMusic = async () => {
  const { result } = await request('libraryItems');
  return (result || []).reduce(flatByAlbum, [])
    .sort((a, b) => String(a.album).localeCompare(String(b.album)));
};

const MusicShelf = ({ onPlay }) => {
  const items = useShelf(loadMusic, [LIBRARY_SCANNED_TOPIC]);
  return (
    <Shelf items={items}>
      {(items || []).map((entry, index) => (
        <Tile
          Icon={LibraryMusicIcon}
          image={entry.cover_url}
          key={entry.content_uri || `${entry.provider}:${entry.albumartist}:${entry.album}:${index}`}
          loadImage={albumCover(entry)}
          onClick={() => {
            request('play_album', {
              album: entry.album, albumartist: entry.albumartist, content_uri: entry.content_uri,
              provider: entry.provider,
            });
            onPlay();
          }}
          subtitle={entry.albumartist}
          title={entry.album}
        />
      ))}
    </Shelf>
  );
};

const loadBooks = async () => ((await request('audiobooksList')).result || []).filter((book) => !book.hidden);

const BookTile = ({ book, onPlay }) => (
  <Tile
    Icon={AutoStoriesIcon}
    image={book.cover_url ? coverSrc(book.cover_url) : undefined}
    onClick={() => {
      request('audiobook_play', { book: book.book, ...sourceArg(book) });
      onPlay();
    }}
    progress={book.finished ? 0 : progressOf(book)}
    title={book.title}
  />
);

const AudiobooksShelf = ({ onPlay }) => {
  const items = useShelf(loadBooks, [LIBRARY_SCANNED_TOPIC]);
  return (
    <Shelf items={items}>
      {(items || []).map((book) => <BookTile book={book} key={`${book.source}/${book.book}`} onPlay={onPlay} />)}
    </Shelf>
  );
};

const loadStations = async () => (await request('radioStations')).result || [];

const StationTile = ({ onPlay, station }) => (
  <Tile
    Icon={RadioIcon}
    image={station.logo || undefined}
    onClick={() => {
      request('radio_play', { station: station.id });
      onPlay();
    }}
    title={station.name}
  />
);

const RadioShelf = ({ onPlay }) => {
  const items = useShelf(loadStations, [RADIO_TOPIC]);
  return (
    <Shelf items={items}>
      {(items || []).map((station) => <StationTile key={station.id} onPlay={onPlay} station={station} />)}
    </Shelf>
  );
};

const loadPodcasts = async () => ((await request('podcastsList')).result || []).filter((podcast) => !podcast.hidden);

const PodcastTile = ({ onOpen, podcast }) => (
  <Tile
    Icon={PodcastsIcon}
    image={podcast.image || undefined}
    onClick={() => onOpen(podcast)}
    subtitle={podcast.unheard > 0 ? `${podcast.unheard}` : undefined}
    title={podcast.name}
  />
);

const PodcastsShelf = ({ onOpen }) => {
  const items = useShelf(loadPodcasts, [PODCASTS_TOPIC]);
  return (
    <Shelf items={items}>
      {(items || []).map((podcast) => <PodcastTile key={podcast.id} onOpen={onOpen} podcast={podcast} />)}
    </Shelf>
  );
};

// The episodes of one podcast, newest first as the backend lists them.
const Episodes = ({ onBack, onPlay, podcast }) => {
  const { t, i18n } = useTranslation();
  const load = useCallback(async () => (await request('podcastEpisodes', { podcast: podcast.id })).result || [],
    [podcast.id]);
  const episodes = useShelf(load, [PODCASTS_TOPIC]);

  const play = (episode) => {
    request('podcast_play', { podcast: podcast.id, ...(episode ? { episode: episode.id } : {}) });
    onPlay();
  };
  const date = (iso) => {
    try {
      return iso ? new Date(iso).toLocaleDateString(i18n.language, { day: 'numeric', month: 'short' }) : '';
    }
    catch {
      return '';
    }
  };

  return (
    <Stack spacing={1} sx={{ padding: 1.5 }}>
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
        <Button onClick={onBack} startIcon={<ArrowBackIcon />} variant="outlined">{t('kiosk.back')}</Button>
        <Typography sx={{ flex: 1, minWidth: 0 }} noWrap variant="h6">{podcast.name}</Typography>
        <Button onClick={() => play()} startIcon={<PlayArrowIcon />} variant="contained">{t('kiosk.play-next')}</Button>
      </Stack>
      {episodes === null && <CircularProgress />}
      {episodes && !episodes.length && <Typography color="text.secondary">{t('kiosk.empty')}</Typography>}
      <List>
        {(episodes || []).map((episode) => (
          <ListItem disablePadding key={episode.id}>
            <ListItemButton onClick={() => play(episode)} sx={{ minHeight: 64 }}>
              <ListItemText
                primary={episode.title}
                secondary={[date(episode.published), episode.duration ? toHHMMSS(episode.duration) : null,
                  episode.heard ? t('library.podcasts.heard') : null].filter(Boolean).join(' · ')}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Stack>
  );
};

const RECENT_STATIONS = 8;

// Audiobooks in progress, podcasts with unheard episodes and the stations played last, as the web app's "Continue".
const ContinueShelf = ({ onOpen, onPlay }) => {
  const load = useCallback(async () => {
    const [books, podcasts, stations] = await Promise.all([loadBooks(), loadPodcasts(), loadStations()]);
    return [
      ...books.filter((book) => !book.finished && progressOf(book) > 0).map((book) => ({ book, kind: 'book' })),
      ...podcasts.filter((podcast) => podcast.unheard > 0).map((podcast) => ({ kind: 'podcast', podcast })),
      ...stations.filter((station) => station.last_played)
        .sort((a, b) => b.last_played.localeCompare(a.last_played))
        .slice(0, RECENT_STATIONS).map((station) => ({ kind: 'station', station })),
    ];
  }, []);
  const items = useShelf(load, [LIBRARY_SCANNED_TOPIC, PODCASTS_TOPIC, RADIO_TOPIC]);
  return (
    <Shelf items={items}>
      {(items || []).map((entry) => {
        if (entry.kind === 'book') {
          return <BookTile book={entry.book} key={`b${entry.book.source}/${entry.book.book}`} onPlay={onPlay} />;
        }
        if (entry.kind === 'podcast') {
          return <PodcastTile key={`p${entry.podcast.id}`} onOpen={onOpen} podcast={entry.podcast} />;
        }
        return <StationTile key={`s${entry.station.id}`} onPlay={onPlay} station={entry.station} />;
      })}
    </Shelf>
  );
};

export { AudiobooksShelf, ContinueShelf, Episodes, MusicShelf, PodcastsShelf, RadioShelf };
