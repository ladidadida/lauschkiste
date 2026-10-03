import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Alert, Button, CircularProgress } from '@mui/material';

import request from '../../utils/request';

const RestartContext = createContext({ refresh: () => {} });

const RESTART_POLL_MS = 2000;
const RESTART_TIMEOUT_MS = 120000;

// Whether settings or plugins wait for a restart; children call `refresh()` after a change.
const RestartProvider = ({ children }) => {
  const [required, setRequired] = useState(false);

  const refresh = useCallback(async () => {
    const { result } = await request('restartState');
    setRequired(Boolean(result?.required));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <RestartContext.Provider value={{ refresh, required }}>
      {children}
    </RestartContext.Provider>
  );
};

const useRestart = () => useContext(RestartContext);

// Offers a restart while one is pending, and waits until Lauschkiste is back.
const RestartBanner = () => {
  const { t } = useTranslation();
  const { required, refresh } = useRestart();
  const [restarting, setRestarting] = useState(false);

  const restart = async () => {
    setRestarting(true);
    await request('restartService');
    const deadline = Date.now() + RESTART_TIMEOUT_MS;
    await new Promise((resolve) => setTimeout(resolve, RESTART_POLL_MS * 2));
    while (Date.now() < deadline) {
      const { result } = await request('restartState');
      if (result && !result.required) break;
      await new Promise((resolve) => setTimeout(resolve, RESTART_POLL_MS));
    }
    setRestarting(false);
    refresh();
  };

  if (!required && !restarting) return null;

  return (
    <Alert
      action={
        <Button color="inherit" disabled={restarting} onClick={restart} size="small">
          {restarting ? <CircularProgress color="inherit" size={18} /> : t('settings.restart.button')}
        </Button>
      }
      severity="warning"
      sx={{ width: '100%' }}
    >
      {restarting ? t('settings.restart.running') : t('settings.restart.required')}
    </Alert>
  );
};

export { RestartBanner, RestartProvider, useRestart };
