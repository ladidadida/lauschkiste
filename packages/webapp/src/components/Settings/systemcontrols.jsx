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

// Only shown with a board support plugin, which can shut the box down and reboot it.
const SystemControls = () => {
  const { t } = useTranslation();
  const [board, setBoard] = useState(null);

  useEffect(() => {
    request('hardwareState').then(({ result }) => setBoard(result?.board || null));
  }, []);

  if (!board) {
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
