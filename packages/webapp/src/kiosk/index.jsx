import { createRoot } from 'react-dom/client';
import { StyledEngineProvider } from '@mui/material/styles';

import AppSettingsProvider from '../context/appsettings';
import PlayerProvider from '../context/player';
import PubSubProvider from '../context/pubsub';
import { i18nReady } from '../i18n';
import KioskApp from './app';

const root = createRoot(document.querySelector('#root'));

i18nReady.then(() => {
  root.render(
    <StyledEngineProvider injectFirst>
      <PubSubProvider>
        <PlayerProvider>
          <AppSettingsProvider>
            <KioskApp />
          </AppSettingsProvider>
        </PlayerProvider>
      </PubSubProvider>
    </StyledEngineProvider>,
  );
});
