import { useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import Alert from '@mui/material/Alert';

import PlayerContext from '../../context/player/context';
import request from '../../utils/request';
import { PLAYER_STATUS_TOPIC } from '../../config';

const REFRESH_MS = 30000;
const WARN_BELOW_SEC = 5 * 60;

// What the time limits plugin (if it runs) says: quiet hours, the day's time used up, or not much left.
const TimeLimitNotice = () => {
  const { t } = useTranslation();
  const { state: { [PLAYER_STATUS_TOPIC]: playerstatus } } = useContext(PlayerContext);
  const [status, setStatus] = useState(null);
  const state = playerstatus?.state;

  useEffect(() => {
    let active = true;
    const load = async () => {
      const { result } = await request('timeLimitsStatus');
      if (active) setStatus(result || null);
    };
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [state]);

  if (!status) return null;
  if (status.blocked) {
    return (
      <Alert severity="info" sx={{ margin: 1, width: '100%' }}>
        {status.reason === 'quiet'
          ? t('player.time-limit.quiet', { until: status.until })
          : t('player.time-limit.used-up')}
      </Alert>
    );
  }
  if (status.remaining_seconds != null && status.remaining_seconds <= WARN_BELOW_SEC && state === 'play') {
    return (
      <Alert severity="warning" sx={{ margin: 1, width: '100%' }}>
        {t('player.time-limit.little-left', { minutes: Math.max(1, Math.ceil(status.remaining_seconds / 60)) })}
      </Alert>
    );
  }
  return null;
};

export default TimeLimitNotice;
