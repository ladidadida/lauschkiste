import { Stack } from '@mui/material';

import Header from '../../Header';
import { RestartBanner } from '../restart';

// A settings subpage: header with the way back, the restart notice, then its cards.
const SettingsPage = ({ children, title }) => (
  <>
    <Header backLink="/settings" title={title} />
    <Stack spacing={1} sx={{ padding: '10px', width: '100%' }}>
      <RestartBanner />
      {children}
    </Stack>
  </>
);

export default SettingsPage;
