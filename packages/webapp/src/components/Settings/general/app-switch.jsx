import { useContext } from 'react';
import { useTranslation } from 'react-i18next';

import {
  Box,
  Grid,
  Switch,
  Typography,
} from '@mui/material';

import AppSettingsContext from '../../../context/appsettings/context';
import request from '../../../utils/request';

// A switch for one boolean web app setting; `name` is the setting and the key below `settings.general` in the texts.
const AppSwitch = ({ name }) => {
  const { t } = useTranslation();
  const { settings, setSettings } = useContext(AppSettingsContext);
  const hint = t(`settings.general.${name}.hint`, { defaultValue: '' });

  const handleSwitch = (event) => {
    const { checked } = event.target;
    setSettings((current) => ({ ...current, [name]: checked }));
    request('setAppSettings', { settings: { [name]: checked } });
  };

  return (
    <Grid container sx={{ flexDirection: 'column', justifyContent: 'center' }}>
      <Grid container sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography>{t(`settings.general.${name}.title`)}</Typography>
        <Box sx={{ alignItems: 'center', display: 'flex', marginLeft: '0' }}>
          <Switch checked={Boolean(settings[name])} onChange={handleSwitch} />
        </Box>
      </Grid>
      {hint && <Typography color="text.secondary" variant="body2">{hint}</Typography>}
    </Grid>
  );
};

export default AppSwitch;
