import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  Alert,
  Avatar,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Stack,
  TextField,
  Typography,
} from '@mui/material';

import CheckIcon from '@mui/icons-material/Check';
import PodcastsIcon from '@mui/icons-material/Podcasts';

import request, { requestErrorMessage } from '../../../utils/request';

const SEARCH_DELAY_MS = 400;

// Search the podcast directories (added by a plugin) and subscribe to what is found; without a search
// term the popular podcasts are shown.
const PodcastSearch = ({ directories, onAddByAddress, onClose, onSubscribed, open }) => {
  const { t } = useTranslation();
  const [term, setTerm] = useState('');
  const [directory, setDirectory] = useState(null);
  const [hits, setHits] = useState([]);
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  const find = useCallback(async () => {
    setIsLoading(true);
    const args = directory ? { directory } : {};
    const { result, error } = term.trim()
      ? await request('podcastSearch', { term: term.trim(), ...args })
      : await request('podcastTop', args);
    setIsLoading(false);
    setMessage(error ? requestErrorMessage(error) || t('library.loading-error') : '');
    setHits(result?.hits || []);
    setErrors(result?.errors || {});
  }, [term, directory, t]);

  useEffect(() => {
    if (!open) return undefined;
    const timer = setTimeout(find, term ? SEARCH_DELAY_MS : 0);
    return () => clearTimeout(timer);
  }, [open, find, term]);

  const subscribe = async (hit) => {
    const { error } = await request('addPodcast', { url: hit.feed_url, name: hit.title });
    if (error) {
      setMessage(requestErrorMessage(error) || t('library.loading-error'));
      return;
    }
    setHits((current) => current.map((entry) => (entry === hit ? { ...entry, subscribed: true } : entry)));
    onSubscribed();
  };

  const label = (id) => directories.find((entry) => entry.id === id)?.label || id;

  return (
    <Dialog fullWidth maxWidth="sm" onClose={onClose} open={open}>
      <DialogTitle>{t('library.podcasts.search.title')}</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          fullWidth
          label={t('library.podcasts.search.label')}
          margin="dense"
          onChange={(event) => setTerm(event.target.value)}
          size="small"
          value={term}
        />
        {directories.length > 1 &&
          <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 1, paddingY: 1 }}>
            <Chip
              color={directory ? 'default' : 'primary'}
              label={t('library.music.all-sources')}
              onClick={() => setDirectory(null)}
            />
            {directories.map(({ id, label: name }) => (
              <Chip
                color={directory === id ? 'primary' : 'default'}
                key={id}
                label={name}
                onClick={() => setDirectory(id)}
              />
            ))}
          </Stack>
        }
        {message && <Alert severity="warning" sx={{ marginY: 1 }}>{message}</Alert>}
        {Object.entries(errors).map(([id, text]) => (
          <Alert key={id} severity="info" sx={{ marginY: 1 }}>{`${label(id)}: ${text}`}</Alert>
        ))}
        {!term.trim() && !isLoading && hits.length > 0 &&
          <Typography color="text.secondary" sx={{ paddingTop: 1 }} variant="body2">
            {t('library.podcasts.search.popular')}
          </Typography>
        }
        {isLoading && <CircularProgress size={24} sx={{ display: 'block', margin: 2 }} />}
        {!isLoading && !hits.length && !message &&
          <Typography sx={{ paddingY: 2 }}>{t('library.podcasts.search.none')}</Typography>
        }
        <List dense>
          {hits.map((hit) => (
            <ListItem
              key={`${hit.directory}/${hit.feed_url}`}
              secondaryAction={hit.subscribed
                ? <CheckIcon aria-label={t('library.podcasts.search.subscribed')} color="success" />
                : <Button onClick={() => subscribe(hit)} size="small">{t('library.podcasts.subscribe')}</Button>}
            >
              <ListItemAvatar>
                <Avatar alt="" src={hit.image || undefined} variant="rounded">
                  <PodcastsIcon />
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary={hit.title}
                secondary={[hit.author, directories.length > 1 ? label(hit.directory) : null].filter(Boolean).join(' · ')}
                slotProps={{ primary: { noWrap: true }, secondary: { noWrap: true } }}
                sx={{ paddingRight: 8 }}
              />
            </ListItem>
          ))}
        </List>
      </DialogContent>
      <DialogActions>
        <Button onClick={onAddByAddress}>{t('library.podcasts.search.by-address')}</Button>
        <Button onClick={onClose}>{t('general.buttons.cancel')}</Button>
      </DialogActions>
    </Dialog>
  );
};

export default PodcastSearch;
