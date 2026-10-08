import { useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
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

export const AudiobookItem = ({ book, onChanged, showCovers }) => {
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

  const menuItems = [
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
            </Box>
          }
          secondary={
            <Box component="span" sx={{ display: 'block' }}>
              <Box component="span" sx={{ display: 'block' }}>{`${status}${duration}`}</Box>
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

  const visible = useMemo(() => {
    const query = musicFilter.toLowerCase();
    return query ? books.filter(({ title }) => title.toLowerCase().includes(query)) : books;
  }, [books, musicFilter]);

  if (isLoading) return <CircularProgress />;
  if (error) return <Typography>{t('library.loading-error')}</Typography>;
  if (!books.length) return <Typography sx={{ padding: 1 }}>{t('library.audiobooks.empty')}</Typography>;
  if (!visible.length) return <Typography>{t('library.albums.no-music')}</Typography>;

  return (
    <List sx={{ width: '100%' }}>
      {visible.map((book) => (
        <AudiobookItem book={book} key={`${book.source}/${book.book}`} onChanged={load} showCovers={showCovers} />
      ))}
    </List>
  );
};

export default Audiobooks;
