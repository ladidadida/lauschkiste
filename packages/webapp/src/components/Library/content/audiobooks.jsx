import { useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  Alert,
  Avatar,
  Box,
  Chip,
  CircularProgress,
  LinearProgress,
  List,
  ListItem,
  ListItemAvatar,
  ListItemButton,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material';

import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DownloadDoneIcon from '@mui/icons-material/DownloadDone';
import MenuBookIcon from '@mui/icons-material/MenuBook';

import AppSettingsContext from '../../../context/appsettings/context';
import PubSubContext from '../../../context/pubsub/context';
import request from '../../../utils/request';
import { coverSrc, toHHMMSS } from '../../../utils/utils';
import { LIBRARY_SCANNED_TOPIC } from '../../../config';
import ItemMenu from './item-menu';

export const progressOf = ({ duration, finished, listened }) => {
  if (finished) return 100;
  if (!duration) return 0;
  return Math.min(100, Math.round((listened / duration) * 100));
};

// Books of other sources (not the local library) name their source in every request.
const sourceArg = (book) => (book.source && book.source !== 'local' ? { source: book.source } : {});

export const AudiobookItem = ({ book, download, onChanged, showCovers, showOrigin = false }) => {
  const { t } = useTranslation();
  const progress = progressOf(book);
  const started = progress > 0 && !book.finished;

  const status = book.finished
    ? t('library.audiobooks.finished')
    : started
      ? t('library.audiobooks.progress', {
        chapter: book.chapter + 1,
        chapters: book.chapters,
        progress,
      })
      : t('library.audiobooks.chapters', { count: book.chapters });
  const duration = book.duration ? ` · ${toHHMMSS(book.duration)}` : '';
  const isLocal = book.source === undefined || book.source === 'local';
  const availability = isLocal
    ? 'local'
    : { done: 'cached' }[download?.state] || (download === undefined ? null : 'stream');
  const origin = [
    isLocal ? null : t(`library.sources.${book.source}`, { defaultValue: book.source }),
    availability && (showOrigin || !isLocal) && t(`library.origin.${availability}`),
  ].filter(Boolean).join(' · ');

  const setFinished = async (finished) => {
    await request('audiobookSetFinished', { book: book.book, finished, ...sourceArg(book) });
    onChanged();
  };

  const downloadState = download?.state;
  const downloadPercent = download?.total ? Math.floor((100 * download.done) / download.total) : 0;
  const downloadStatus = {
    queued: t('library.audiobooks.queued'),
    downloading: t('library.audiobooks.downloading', { progress: downloadPercent }),
    error: t('library.audiobooks.download-error'),
    done: download?.update_available ? t('library.audiobooks.update-available') : undefined,
  }[downloadState];
  const downloadRequest = async (command) => {
    await request(command, { source: book.source, item: book.book });
    onChanged();
  };
  const downloadItem = (() => {
    if (book.source === undefined || book.source === 'local') return [];
    if (downloadState === 'done') {
      return [
        ...(download.update_available
          ? [{
            label: t('library.audiobooks.download-again'),
            onClick: async () => {
              await request('cacheRemove', { source: book.source, item: book.book });
              await downloadRequest('cacheDownload');
            },
          }]
          : []),
        { label: t('library.audiobooks.remove-download'), onClick: () => downloadRequest('cacheRemove') },
      ];
    }
    if (downloadState === 'downloading' || downloadState === 'queued') {
      return [{ label: t('library.audiobooks.cancel-download'), onClick: () => downloadRequest('cacheCancel') }];
    }
    return [{ label: t('library.audiobooks.download'), onClick: () => downloadRequest('cacheDownload') }];
  })();

  const menuItems = [
    ...downloadItem,
    {
      label: t('library.audiobooks.restart'),
      onClick: () => request('audiobook_restart', { book: book.book, ...sourceArg(book) }).then(onChanged),
    },
    book.finished
      ? { label: t('library.audiobooks.mark-unfinished'), onClick: () => setFinished(false) }
      : { label: t('library.audiobooks.mark-finished'), onClick: () => setFinished(true) },
  ];

  return (
    <ListItem
      disablePadding
      secondaryAction={<ItemMenu items={menuItems} label={t('library.audiobooks.menu', { title: book.title })} />}
    >
      <ListItemButton onClick={() => request('audiobook_play', { book: book.book, ...sourceArg(book) })}>
        {showCovers &&
          <ListItemAvatar>
            <Avatar alt="" src={book.cover_url ? coverSrc(book.cover_url) : undefined} variant="rounded">
              <MenuBookIcon />
            </Avatar>
          </ListItemAvatar>
        }
        <ListItemText
          primary={
            <Box component="span" sx={{ alignItems: 'center', display: 'flex', gap: 0.5 }}>
              {book.title}
              {book.finished && <CheckCircleIcon color="success" fontSize="small" titleAccess={status} />}
              {downloadState === 'done' &&
                <DownloadDoneIcon fontSize="small" titleAccess={t('library.audiobooks.downloaded')} />}
            </Box>
          }
          secondary={
            <Box component="span" sx={{ display: 'block' }}>
              <Box component="span" sx={{ display: 'block' }}>{`${status}${duration}`}</Box>
              {downloadStatus && <Box component="span" sx={{ display: 'block' }}>{downloadStatus}</Box>}
              {origin && <Box component="span" sx={{ color: 'text.disabled', display: 'block', fontSize: '0.8em' }}>{origin}</Box>}
              {started &&
                <LinearProgress
                  aria-label={t('library.audiobooks.progress-label', { title: book.title })}
                  component="span"
                  sx={{ display: 'block', marginTop: 0.5 }}
                  value={progress}
                  variant="determinate"
                />
              }
            </Box>
          }
        />
      </ListItemButton>
    </ListItem>
  );
};

const Audiobooks = ({ musicFilter }) => {
  const { t } = useTranslation();
  const [books, setBooks] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const { settings: { show_covers: showCovers } = {} } = useContext(AppSettingsContext);
  const { state: { [LIBRARY_SCANNED_TOPIC]: lastScan } = {} } = useContext(PubSubContext);

  const load = useCallback(async () => {
    const { result, error: requestError } = await request('audiobooksList');
    setIsLoading(false);
    setError(requestError || null);
    if (result) setBooks(result);
  }, []);

  useEffect(() => {
    load();
  }, [load, lastScan]);

  const [downloads, setDownloads] = useState({});
  const loadDownloads = useCallback(async () => {
    const { result } = await request('cacheDownloads');
    setDownloads(result ? Object.fromEntries(result.items.map((entry) => [`${entry.source}/${entry.item}`, entry])) : {});
  }, []);
  const hasRemoteBooks = books.some(({ source }) => source && source !== 'local');
  useEffect(() => {
    if (hasRemoteBooks) loadDownloads();
  }, [hasRemoteBooks, loadDownloads]);
  const downloading = Object.values(downloads).some(({ state }) => state === 'downloading' || state === 'queued');
  useEffect(() => {
    if (!downloading) return undefined;
    const timer = setInterval(loadDownloads, 3000);
    return () => clearInterval(timer);
  }, [downloading, loadDownloads]);
  const [serverStatus, setServerStatus] = useState(null);
  const loadStatus = useCallback(async () => {
    const { result } = await request('audiobookshelfStatus');
    setServerStatus(result || null);
  }, []);
  useEffect(() => {
    if (hasRemoteBooks || !books.length) loadStatus();
  }, [hasRemoteBooks, books, loadStatus]);
  const changed = useCallback(() => {
    load();
    loadDownloads();
    loadStatus();
  }, [load, loadDownloads, loadStatus]);

  const [source, setSource] = useState(null);
  const sources = useMemo(() => [...new Set(books.map((entry) => entry.source || 'local'))], [books]);
  const visible = useMemo(() => {
    const query = musicFilter.toLowerCase();
    return books
      .filter((entry) => !source || (entry.source || 'local') === source)
      .filter(({ title }) => !query || title.toLowerCase().includes(query));
  }, [books, musicFilter, source]);

  if (isLoading) return <CircularProgress />;
  if (error) return <Typography>{t('library.loading-error')}</Typography>;
  if (!books.length) return <Typography sx={{ padding: 1 }}>{t('library.audiobooks.empty')}</Typography>;
  if (!visible.length) return <Typography>{t('library.albums.no-music')}</Typography>;

  return (
    <>
      {serverStatus?.configured && !serverStatus.reachable &&
        <Alert severity="warning" sx={{ marginBottom: 1 }}>
          {t('library.audiobooks.server-down', { error: serverStatus.error || '' })}
          {serverStatus.waiting > 0 && ` ${t('library.audiobooks.waiting', { count: serverStatus.waiting })}`}
        </Alert>
      }
      {sources.length > 1 &&
        <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 1, paddingX: 1, paddingBottom: 1 }}>
          <Chip
            color={source ? 'default' : 'primary'}
            label={t('library.music.all-sources')}
            onClick={() => setSource(null)}
          />
          {sources.map((id) => (
            <Chip
              color={source === id ? 'primary' : 'default'}
              key={id}
              label={t(`library.sources.${id}`, { defaultValue: id })}
              onClick={() => setSource(id)}
            />
          ))}
        </Stack>
      }
      <List sx={{ width: '100%' }}>
        {visible.map((book) => (
          <AudiobookItem
            book={book}
            download={downloads[`${book.source}/${book.book}`] ?? null}
            key={`${book.source}/${book.book}`}
            onChanged={changed}
            showCovers={showCovers}
            showOrigin={sources.length > 1}
          />
        ))}
      </List>
    </>
  );
};

export default Audiobooks;
