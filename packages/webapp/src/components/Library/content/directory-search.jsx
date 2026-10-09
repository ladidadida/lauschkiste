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

import request, { requestErrorMessage } from '../../../utils/request';

const SEARCH_DELAY_MS = 400;

// Search the directories a plugin added (for podcasts or radio stations) and add what is found; without a search
// term the popular ones are shown. `kind` selects the commands and texts; `describe(hit)` gives the line of a hit.
const DirectorySearch = ({ directories, kind, onAddByAddress, onChanged, onClose, open }) => {
  const { t } = useTranslation();
  const [term, setTerm] = useState('');
  const [directory, setDirectory] = useState(null);
  const [hits, setHits] = useState([]);
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { Icon, add, describe, search, texts, top } = kind;

  const find = useCallback(async () => {
    setIsLoading(true);
    const args = directory ? { directory } : {};
    const { result, error } = term.trim()
      ? await request(search, { term: term.trim(), ...args })
      : await request(top, args);
    setIsLoading(false);
    setMessage(error ? requestErrorMessage(error) || t('library.loading-error') : '');
    setHits(result?.hits || []);
    setErrors(result?.errors || {});
  }, [term, directory, t, search, top]);

  useEffect(() => {
    if (!open) return undefined;
    const timer = setTimeout(find, term ? SEARCH_DELAY_MS : 0);
    return () => clearTimeout(timer);
  }, [open, find, term]);

  const choose = async (hit) => {
    const { error } = await request(add.command, add.args(hit));
    if (error) {
      setMessage(requestErrorMessage(error) || t('library.loading-error'));
      return;
    }
    setHits((current) => current.map((entry) => (entry === hit ? { ...entry, [add.doneField]: true } : entry)));
    onChanged();
  };

  const label = (id) => directories.find((entry) => entry.id === id)?.label || id;

  return (
    <Dialog fullWidth maxWidth="sm" onClose={onClose} open={open}>
      <DialogTitle>{t(`${texts}.title`)}</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          fullWidth
          label={t(`${texts}.label`)}
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
            {t(`${texts}.popular`)}
          </Typography>
        }
        {isLoading && <CircularProgress size={24} sx={{ display: 'block', margin: 2 }} />}
        {!isLoading && !hits.length && !message &&
          <Typography sx={{ paddingY: 2 }}>{t(`${texts}.none`)}</Typography>
        }
        <List dense>
          {hits.map((hit) => {
            const { key, title, details, image, done } = describe(hit, directories.length > 1 ? label(hit.directory) : null);
            return (
              <ListItem
                key={key}
                secondaryAction={done
                  ? <CheckIcon aria-label={t(`${texts}.done`)} color="success" />
                  : <Button onClick={() => choose(hit)} size="small">{t(`${texts}.choose`)}</Button>}
              >
                <ListItemAvatar>
                  <Avatar alt="" src={image || undefined} variant="rounded">
                    <Icon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={title}
                  secondary={details}
                  slotProps={{ primary: { noWrap: true }, secondary: { noWrap: true } }}
                  sx={{ paddingRight: 8 }}
                />
              </ListItem>
            );
          })}
        </List>
      </DialogContent>
      <DialogActions>
        <Button onClick={onAddByAddress}>{t(`${texts}.by-address`)}</Button>
        <Button onClick={onClose}>{t('general.buttons.cancel')}</Button>
      </DialogActions>
    </Dialog>
  );
};

export default DirectorySearch;
