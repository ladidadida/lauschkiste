import { useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  Alert,
  Avatar,
  Box,
  CircularProgress,
  LinearProgress,
  List,
  ListItem,
  ListItemAvatar,
  ListItemButton,
  ListItemText,
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

export const AudiobookItem = ({ book, download, onChanged, showCovers }) => {
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
    await request(command, { book: book.book });
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
              await request('audiobookshelfRemoveDownload', { book: book.book });
              await downloadRequest('audiobookshelfDownload');
            },
          }]
          : []),
        { label: t('library.audiobooks.remove-download'), onClick: () => downloadRequest('audiobookshelfRemoveDownload') },
      ];
    }
    if (downloadState === 'downloading' || downloadState === 'queued') {
      return [{ label: t('library.audiobooks.cancel-download'), onClick: () => downloadRequest('audiobookshelfCancelDownload') }];
    }
    return [{ label: t('library.audiobooks.download'), onClick: () => downloadRequest('audiobookshelfDownload') }];
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
    const { result } = await request('audiobookshelfDownloads');
    setDownloads(result ? Object.fromEntries(result.items.map((entry) => [entry.book, entry])) : {});
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

  const visible = useMemo(() => {
    const query = musicFilter.toLowerCase();
    return query ? books.filter(({ title }) => title.toLowerCase().includes(query)) : books;
  }, [books, musicFilter]);

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
      <List sx={{ width: '100%' }}>
        {visible.map((book) => (
          <AudiobookItem
            book={book}
            download={downloads[book.book]}
            key={`${book.source}/${book.book}`}
            onChanged={changed}
            showCovers={showCovers}
          />
        ))}
      </List>
    </>
  );
};

export default Audiobooks;
