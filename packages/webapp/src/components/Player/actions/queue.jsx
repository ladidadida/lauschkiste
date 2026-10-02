import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListSubheader,
} from '@mui/material';

import QueueMusicIcon from '@mui/icons-material/QueueMusic';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';

import request from '../../../utils/request';
import { toHHMMSS } from '../../../utils/utils';

// "Up next": the queue (songs or chapters); tap an entry to play it.
const Queue = ({ kind, position, length }) => {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [entries, setEntries] = useState([]);

  useEffect(() => {
    if (open) request('playerQueue').then(({ result }) => setEntries(result || []));
  }, [open, length]);

  const label = t(`player.queue.title.${kind}`);

  return (
    <>
      <IconButton aria-label={label} disabled={length < 2} onClick={() => setOpen(true)} title={label}>
        <QueueMusicIcon />
      </IconButton>
      <Drawer anchor="bottom" onClose={() => setOpen(false)} open={open}
        slotProps={{ paper: { sx: { maxHeight: '70vh' } } }}>
        <List subheader={<ListSubheader>{label}</ListSubheader>}>
          {entries.map((entry) => (
            <ListItem disablePadding key={entry.position}>
              <ListItemButton
                onClick={() => {
                  request('jump', { position: entry.position });
                  setOpen(false);
                }}
                selected={entry.position === position}
              >
                <ListItemText
                  primary={entry.title || entry.file.split('/').pop()}
                  secondary={entry.duration ? toHHMMSS(entry.duration) : null}
                />
                {entry.position === position && <VolumeUpIcon color="primary" fontSize="small" />}
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Drawer>
    </>
  );
};

export default Queue;
