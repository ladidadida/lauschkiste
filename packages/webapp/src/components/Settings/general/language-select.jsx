import { useContext } from 'react';
import { useTranslation } from 'react-i18next';

import { MenuItem, TextField, Typography } from '@mui/material';

import AppSettingsContext from '../../../context/appsettings/context';
import request from '../../../utils/request';

const LANGUAGES = ['auto', 'de', 'en'];

const LanguageSelect = () => {
  const { t } = useTranslation();
  const { settings, setSettings } = useContext(AppSettingsContext);

  const handleChange = (event) => {
    const { value } = event.target;
    setSettings((current) => ({ ...current, language: value }));
    request('setAppSettings', { settings: { language: value } });
  };

  return (
    <>
      <TextField
        fullWidth
        label={t('settings.language.title')}
        onChange={handleChange}
        select
        size="small"
        value={settings.language || 'auto'}
      >
        {LANGUAGES.map((code) => (
          <MenuItem key={code} value={code}>{t(`settings.language.${code}`)}</MenuItem>
        ))}
      </TextField>
      <Typography color="text.secondary" sx={{ marginTop: 1 }} variant="body2">{t('settings.language.hint')}</Typography>
    </>
  );
};

export default LanguageSelect;
