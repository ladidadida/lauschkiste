import { useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  Avatar,
  Box,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemAvatar,
  ListItemButton,
  ListItemText,
  Typography,
} from '@mui/material';

import AddIcon from '@mui/icons-material/Add';
import RadioIcon from '@mui/icons-material/Radio';

import PubSubContext from '../../../context/pubsub/context';
import request from '../../../utils/request';
import { RADIO_TOPIC } from '../../../config';
import ConfirmDialog from './confirm-dialog';
import FormDialog from './form-dialog';
import ItemMenu from './item-menu';

const Radio = ({ musicFilter }) => {
  const { t } = useTranslation();
  const [stations, setStations] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const { state: { [RADIO_TOPIC]: changed } = {} } = useContext(PubSubContext);

  const load = useCallback(async () => {
    const { result, error: requestError } = await request('radioStations');
    setIsLoading(false);
    setError(requestError || null);
    if (result) setStations(result);
  }, []);

  useEffect(() => {
    if (changed?.stations) {
      setStations(changed.stations);
      setIsLoading(false);
    }
    else {
      load();
    }
  }, [changed, load]);

  const visible = useMemo(() => {
    const query = musicFilter.toLowerCase();
    return query ? stations.filter(({ name }) => name.toLowerCase().includes(query)) : stations;
  }, [stations, musicFilter]);

  const fields = [
    { name: 'name', label: t('library.radio.name'), required: true },
    { name: 'url', label: t('library.radio.url'), required: true, type: 'url', helperText: t('library.radio.url-help') },
    { name: 'logo', label: t('library.radio.logo'), type: 'url' },
  ];

  const save = (values) => (
    editing?.id
      ? request('updateRadioStation', { station: editing.id, ...values })
      : request('addRadioStation', { ...values, logo: values.logo || undefined })
  );

  const remove = async () => {
    await request('deleteRadioStation', { station: deleting.id });
    setDeleting(null);
    load();
  };

  if (isLoading) return <CircularProgress />;
  if (error) return <Typography>{t('library.loading-error')}</Typography>;

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', paddingX: 1 }}>
        <Button onClick={() => setEditing({})} startIcon={<AddIcon />}>
          {t('library.radio.add')}
        </Button>
      </Box>
      {!stations.length && <Typography sx={{ padding: 1 }}>{t('library.radio.empty')}</Typography>}
      {stations.length > 0 && !visible.length && <Typography>{t('library.albums.no-music')}</Typography>}
      <List sx={{ width: '100%' }}>
        {visible.map((station) => (
          <ListItem
            disablePadding
            key={station.id}
            secondaryAction={
              <ItemMenu
                items={[
                  { label: t('library.radio.edit'), onClick: () => setEditing(station) },
                  { label: t('general.buttons.delete'), onClick: () => setDeleting(station) },
                ]}
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
              <ListItemText
                primary={station.name}
                secondary={station.url}
                slotProps={{ secondary: { noWrap: true } }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <FormDialog
        fields={fields}
        initialValues={editing || {}}
        onClose={() => setEditing(null)}
        onSaved={() => {
          setEditing(null);
          load();
        }}
        onSubmit={save}
        open={Boolean(editing)}
        title={editing?.id ? t('library.radio.edit') : t('library.radio.add')}
      />
      <ConfirmDialog
        onClose={() => setDeleting(null)}
        onConfirm={remove}
        open={Boolean(deleting)}
        text={t('library.radio.delete-text')}
        title={t('library.radio.delete-title', { name: deleting?.name })}
      />
    </Box>
  );
};

export default Radio;
