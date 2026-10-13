import { useTranslation } from 'react-i18next';

import {
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
} from '@mui/material';

import RebootDialog from './dialogs/reboot';
import ShutDownDialog from './dialogs/shutdown';
import { useEffect, useState } from 'react';

import request from '../../utils/request';

// Only shown with a device plugin that can power the machine off, which can shut the box down and reboot it.
const SystemControls = () => {
  const { t } = useTranslation();
  const [device, setDevice] = useState(null);

  useEffect(() => {
    request('hardwareState').then(({ result }) => setDevice(result?.device || null));
  }, []);

  if (!device) {
    return null;
  }

  return (
    <Card>
      <CardHeader title={t('settings.systemcontrols.title')} />
      <Divider />
      <CardContent>
        <Grid
          container
          sx={{
            alignItems: 'center',
            justifyContent: 'space-around',
          }}
        >
          <Grid>
            <RebootDialog />
          </Grid>
          <Grid>
            <ShutDownDialog />
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default SystemControls;
