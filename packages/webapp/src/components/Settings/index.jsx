import { Route, Routes } from 'react-router-dom';

import { Grid } from '@mui/material';

import SettingsOverview from './pages/overview';
import { PluginSettings, PluginsSettings } from './pages/plugins';
import {
  CardSettings, LibrarySettings, PlaybackSettings, StatusSettings, SystemSettings,
} from './pages/sections';
import { RestartProvider } from './restart';

const Settings = () => (
  <RestartProvider>
    <Grid container id="settings" size={12}>
      <Routes>
        <Route index element={<SettingsOverview />} />
        <Route path="status" element={<StatusSettings />} />
        <Route path="playback" element={<PlaybackSettings />} />
        <Route path="cards" element={<CardSettings />} />
        <Route path="library" element={<LibrarySettings />} />
        <Route path="plugins" element={<PluginsSettings />} />
        <Route path="plugins/:name" element={<PluginSettings />} />
        <Route path="system" element={<SystemSettings />} />
      </Routes>
    </Grid>
  </RestartProvider>
);

export default Settings;
