import { useTranslation } from 'react-i18next';

import { useTheme } from '@mui/material/styles';

import {
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
} from '@mui/material';
import AppSwitch from './app-switch';

const SettingsGeneral = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const spacer = { marginBottom: theme.spacing(2) }

  return (
    <Card>
      <CardHeader
        title={t('settings.general.title')}
      />
      <Divider />
      <CardContent>
        <Grid
          container
          sx={{
            '& > .MuiGrid-root:not(:last-child)': spacer,
            flexDirection: 'column',
          }}
        >
          <AppSwitch name="show_covers" />
          <AppSwitch name="on_screen_keyboard" />
        </Grid>
      </CardContent>
    </Card>
  );
};

export default SettingsGeneral;
