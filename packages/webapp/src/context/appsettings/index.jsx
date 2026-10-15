import { useEffect, useState } from 'react';

import AppSettingsContext from './context';
import i18n from '../../i18n';
import request from '../../utils/request';

const AppSettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState({});

  useEffect(() => {
    const loadAppSettings = async () => {
      const { result, error } = await request('getAppSettings');
      if(result) setSettings(result);
      if(error) {
        console.error('Error loading AppSettings');
      }
    }

    loadAppSettings();
  }, []);

  useEffect(() => {
    if (settings.language && settings.language !== 'auto') i18n.changeLanguage(settings.language);
  }, [settings.language]);

  const context = {
    setSettings,
    settings,
  };

  return(
    <AppSettingsContext.Provider value={context}>
      { children }
    </AppSettingsContext.Provider>
  )
};

export default AppSettingsProvider;
