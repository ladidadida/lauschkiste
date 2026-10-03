import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import {
  Button,
  Card,
  CardContent,
  CardHeader,
  Divider,
  List,
  ListItem,
  ListItemText,
  Typography,
} from '@mui/material';

import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';

import request from '../../../utils/request';
import Outputs from '../audio/outputs';
import ModuleSettings from '../form/module-settings';
import SettingsGeneral from '../general';
import SettingsStatus from '../status';
import SystemControls from '../systemcontrols';
import SambaSettings from './samba';
import SettingsPage from './page';

const StatusSettings = () => {
  const { t } = useTranslation();
  return (
    <SettingsPage title={t('settings.sections.status.title')}>
      <SettingsStatus />
    </SettingsPage>
  );
};

const PlaybackSettings = () => {
  const { t } = useTranslation();
  return (
    <SettingsPage title={t('settings.sections.playback.title')}>
      <Card>
        <CardContent><Outputs /></CardContent>
      </Card>
      <ModuleSettings module="volume" />
      <ModuleSettings exclude={['second_swipe_action']} module="player" />
      <ModuleSettings module="audiobooks" />
      <ModuleSettings module="podcasts" />
      <ModuleSettings module="jingle" />
      <ModuleSettings module="input" />
    </SettingsPage>
  );
};

const CardSettings = () => {
  const { t } = useTranslation();
  const [readers, setReaders] = useState(null);

  useEffect(() => {
    request('rfidReaders').then(({ result }) => setReaders(result || {}));
  }, []);

  return (
    <SettingsPage title={t('settings.sections.cards.title')}>
      <Card>
        <CardHeader title={t('settings.cards.list')} />
        <Divider />
        <CardContent>
          <Typography sx={{ marginBottom: 2 }}>{t('settings.cards.list-help')}</Typography>
          <Button component={Link} endIcon={<KeyboardArrowRightIcon />} to="/cards" variant="outlined">
            {t('settings.cards.open-list')}
          </Button>
        </CardContent>
      </Card>
      <ModuleSettings fields={['second_swipe_action']} module="player" title={t('settings.cards.behaviour')} />
      <Card>
        <CardHeader title={t('settings.cards.readers')} />
        <Divider />
        <CardContent>
          {readers && Object.keys(readers).length === 0 &&
            <Typography>{t('settings.cards.no-readers')}</Typography>
          }
          <List dense>
            {Object.entries(readers || {}).map(([key, driver]) => (
              <ListItem key={key}><ListItemText primary={driver} secondary={key} /></ListItem>
            ))}
          </List>
          <Typography color="text.secondary" variant="body2">{t('settings.cards.readers-help')}</Typography>
        </CardContent>
      </Card>
    </SettingsPage>
  );
};

const LibrarySettings = () => {
  const { t } = useTranslation();
  return (
    <SettingsPage title={t('settings.sections.library.title')}>
      <SettingsGeneral />
      <ModuleSettings module="library" />
      <SambaSettings />
    </SettingsPage>
  );
};

const SystemSettings = () => {
  const { t } = useTranslation();
  const [restarting, setRestarting] = useState(false);
  return (
    <SettingsPage title={t('settings.sections.system.title')}>
      <ModuleSettings module="system" />
      <Card>
        <CardHeader title={t('settings.system.service')} />
        <Divider />
        <CardContent>
          <Typography sx={{ marginBottom: 2 }} variant="body2">{t('settings.system.restart-help')}</Typography>
          <Button
            disabled={restarting}
            onClick={() => {
              setRestarting(true);
              request('restartService');
            }}
            variant="outlined"
          >
            {restarting ? t('settings.restart.running') : t('settings.restart.button')}
          </Button>
        </CardContent>
      </Card>
      <SystemControls />
    </SettingsPage>
  );
};

export { CardSettings, LibrarySettings, PlaybackSettings, StatusSettings, SystemSettings };
