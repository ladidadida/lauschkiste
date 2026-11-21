import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  Alert,
  Avatar,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  List,
  ListItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';

import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import MenuBookIcon from '@mui/icons-material/MenuBook';

import request, { requestErrorMessage } from '../../../utils/request';
import { uploadAudiobookCover } from '../../../utils/library-api';
import { coverSrc, toHHMMSS } from '../../../utils/utils';

export const moveItem = (items, index, offset) => {
  const target = index + offset;
  if (target < 0 || target >= items.length) return items;
  const next = [...items];
  [next[index], next[target]] = [next[target], next[index]];
  return next;
};

// Title, author, cover and chapters (order and titles) of a local audiobook; empty fields go back to the tags.
const AudiobookEditor = ({ book, onClose, onSaved, open }) => {
  const { t } = useTranslation();
  const [details, setDetails] = useState(null);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [chapters, setChapters] = useState([]);
  const [error, setError] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const fileInput = useRef(null);

  const load = async () => {
    const { result, error: requestError } = await request('audiobookGet', { book });
    if (requestError) {
      setError(requestErrorMessage(requestError) || t('library.content.save-error'));
      return;
    }
    setDetails(result);
    return result;
  };

  useEffect(() => {
    if (!open) return;
    setError('');
    setDetails(null);
    load().then((result) => {
      if (!result) return;
      setTitle(result.title);
      setAuthor(result.author || '');
      setChapters(result.chapters);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, book]);

  const run = async (call) => {
    setIsBusy(true);
    setError('');
    try {
      return await call();
    }
    catch (callError) {
      setError(callError.message || t('library.content.save-error'));
    }
    finally {
      setIsBusy(false);
    }
  };

  const uploadCover = (event) => {
    const [file] = event.target.files || [];
    event.target.value = '';
    if (!file) return;
    run(async () => {
      await uploadAudiobookCover(book, file);
      await load();
    });
  };

  const removeCover = () => run(async () => {
    await request('audiobookRemoveCover', { book });
    await load();
  });

  const setChapterTitle = (index, value) => {
    setChapters(chapters.map((chapter, position) => (position === index ? { ...chapter, title: value } : chapter)));
  };

  const save = (event) => {
    event.preventDefault();
    run(async () => {
      const { error: requestError } = await request('audiobookEdit', {
        book,
        title: title.trim(),
        author: author.trim(),
        chapters: chapters.map((chapter) => ({ file: chapter.file, title: chapter.title.trim() })),
      });
      if (requestError) {
        setError(requestErrorMessage(requestError) || t('library.content.save-error'));
        return;
      }
      onSaved();
    });
  };

  const close = () => {
    if (!isBusy) onClose();
  };

  return (
    <Dialog fullWidth maxWidth="md" onClose={close} open={open} scroll="paper">
      <form onSubmit={save}>
        <DialogTitle>{t('library.audiobooks.edit')}</DialogTitle>
        <DialogContent dividers>
          {error && <Alert severity="error" sx={{ marginBottom: 2 }}>{error}</Alert>}
          {!details && !error && <CircularProgress />}
          {details &&
            <>
              <Stack direction="row" spacing={2} sx={{ alignItems: 'center', marginBottom: 1 }}>
                <Avatar
                  alt=""
                  src={details.cover_url ? coverSrc(details.cover_url) : undefined}
                  sx={{ height: 96, width: 96 }}
                  variant="rounded"
                >
                  <MenuBookIcon fontSize="large" />
                </Avatar>
                <Stack spacing={1}>
                  <Button disabled={isBusy} onClick={() => fileInput.current?.click()} variant="outlined">
                    {t('library.audiobooks.choose-cover')}
                  </Button>
                  {details.custom_cover &&
                    <Button disabled={isBusy} onClick={removeCover}>{t('library.audiobooks.reset-cover')}</Button>
                  }
                  <input
                    accept="image/jpeg,image/png,image/webp,image/gif"
                    aria-label={t('library.audiobooks.choose-cover')}
                    hidden
                    onChange={uploadCover}
                    ref={fileInput}
                    type="file"
                  />
                </Stack>
              </Stack>
              <TextField
                disabled={isBusy}
                fullWidth
                helperText={t('library.audiobooks.title-help', { title: details.tag_title || book })}
                label={t('library.audiobooks.title-label')}
                margin="dense"
                onChange={(event) => setTitle(event.target.value)}
                value={title}
              />
              <TextField
                disabled={isBusy}
                fullWidth
                helperText={details.tag_author
                  ? t('library.audiobooks.author-help', { author: details.tag_author })
                  : undefined}
                label={t('library.audiobooks.author-label')}
                margin="dense"
                onChange={(event) => setAuthor(event.target.value)}
                value={author}
              />
              <Typography sx={{ marginTop: 2 }} variant="subtitle1">{t('library.audiobooks.chapters-label')}</Typography>
              <List dense>
                {chapters.map((chapter, index) => (
                  <ListItem disableGutters key={chapter.file}>
                    <Box sx={{ alignItems: 'center', display: 'flex', gap: 1, width: '100%' }}>
                      <Typography sx={{ minWidth: 24, textAlign: 'right' }} variant="body2">{index + 1}</Typography>
                      <TextField
                        disabled={isBusy}
                        fullWidth
                        helperText={`${chapter.file}${chapter.duration ? ` · ${toHHMMSS(chapter.duration)}` : ''}`}
                        slotProps={{
                          htmlInput: { 'aria-label': t('library.audiobooks.chapter-label', { number: index + 1 }) },
                        }}
                        onChange={(event) => setChapterTitle(index, event.target.value)}
                        placeholder={chapter.tag_title || ''}
                        size="small"
                        value={chapter.title}
                      />
                      <IconButton
                        aria-label={t('library.audiobooks.move-up', { number: index + 1 })}
                        disabled={isBusy || index === 0}
                        onClick={() => setChapters(moveItem(chapters, index, -1))}
                      >
                        <ArrowUpwardIcon />
                      </IconButton>
                      <IconButton
                        aria-label={t('library.audiobooks.move-down', { number: index + 1 })}
                        disabled={isBusy || index === chapters.length - 1}
                        onClick={() => setChapters(moveItem(chapters, index, 1))}
                      >
                        <ArrowDownwardIcon />
                      </IconButton>
                    </Box>
                  </ListItem>
                ))}
              </List>
            </>
          }
        </DialogContent>
        <DialogActions>
          <Button disabled={isBusy} onClick={close} sx={{ minHeight: 44 }}>{t('general.buttons.cancel')}</Button>
          <Button disabled={isBusy || !details} sx={{ minHeight: 44 }} type="submit" variant="contained">
            {t('general.buttons.save')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default AudiobookEditor;
