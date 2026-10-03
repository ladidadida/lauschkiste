import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import {
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
} from '@mui/material';

import BookmarksIcon from '@mui/icons-material/Bookmarks';
import ExtensionIcon from '@mui/icons-material/Extension';
import InfoIcon from '@mui/icons-material/Info';
import LibraryMusicIcon from '@mui/icons-material/LibraryMusic';
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew';
import TuneIcon from '@mui/icons-material/Tune';

import Header from '../../Header';
import { RestartBanner } from '../restart';

const SECTIONS = [
  ['status', InfoIcon],
  ['playback', TuneIcon],
  ['cards', BookmarksIcon],
  ['library', LibraryMusicIcon],
  ['plugins', ExtensionIcon],
  ['system', PowerSettingsNewIcon],
];

const SettingsOverview = () => {
  const { t } = useTranslation();

  return (
    <>
      <Header title={t('navigation.settings')} />
      <Stack spacing={1} sx={{ padding: '10px', width: '100%' }}>
        <RestartBanner />
        <List>
          {SECTIONS.map(([id, Icon]) => (
            <ListItem disablePadding key={id}>
              <ListItemButton component={Link} nativeButton={false} to={`/settings/${id}`}>
                <ListItemIcon><Icon /></ListItemIcon>
                <ListItemText primary={t(`settings.sections.${id}.title`)}
                  secondary={t(`settings.sections.${id}.subtitle`)} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Stack>
    </>
  );
};

export default SettingsOverview;
