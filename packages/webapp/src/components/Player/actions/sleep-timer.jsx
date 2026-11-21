import { useCallback, useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  IconButton,
  MenuItem,
  Stack,
  Switch,
  TextField,
  Typography,
} from '@mui/material';

import BedtimeIcon from '@mui/icons-material/Bedtime';
import BedtimeOutlinedIcon from '@mui/icons-material/BedtimeOutlined';

import { Countdown } from '../../general';
import PubSubContext from '../../../context/pubsub/context';
import request from '../../../utils/request';
import { TIMERS_TOPIC } from '../../../config';

const MINUTES = [15, 30, 45, 60, 90];
const TIMERS = ['stop_player', 'fade_volume'];

// The sleep timer: stop (optionally fading out) after some minutes, or after the current entry; or at every start.
const SleepTimer = ({ kind, stopAfterCurrent }) => {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [fade, setFade] = useState(true);
  const [timers, setTimers] = useState({});
  const [everyStart, setEveryStart] = useState(0);
  const { state: { [TIMERS_TOPIC]: published } = {} } = useContext(PubSubContext);

  const load = useCallback(async () => {
    const { result } = await request('listTimers');
    setTimers(Object.fromEntries((result || []).filter(({ name }) => TIMERS.includes(name))
      .map((timer) => [timer.name, timer])));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!open) return;
    request('moduleSettings', { name: 'timers' }).then(({ result }) => {
      if (!result) return;
      setEveryStart(result.values.every_start_minutes || 0);
      setFade(result.values.every_start_fade !== false);
    });
  }, [open]);

  const saveEveryStart = async (minutes, fadeOut) => {
    setEveryStart(minutes);
    await request('updateModuleSettings', {
      name: 'timers', values: { every_start_minutes: minutes, every_start_fade: fadeOut },
    });
  };

  const changeFade = (checked) => {
    setFade(checked);
    if (everyStart) saveEveryStart(everyStart, checked);
  };

  useEffect(() => {
    if (published && TIMERS.includes(published.name)) {
      setTimers((current) => ({ ...current, [published.name]: published }));
    }
  }, [published]);

  const running = TIMERS.map((name) => timers[name]).find((timer) => timer?.enabled);
  const isActive = Boolean(running) || stopAfterCurrent;

  const cancelAll = async () => {
    await Promise.all([
      ...TIMERS.filter((name) => timers[name]?.enabled).map((timer) => request('cancelTimer', { timer })),
      stopAfterCurrent ? request('stop_after_current', { enabled: false }) : null,
    ]);
    load();
  };

  const startMinutes = async (minutes) => {
    await cancelAll();
    await request('startTimer', { timer: fade ? 'fade_volume' : 'stop_player', wait_seconds: minutes * 60 });
    setOpen(false);
    load();
  };

  const startEndOfEntry = async () => {
    await cancelAll();
    await request('stop_after_current', { enabled: true });
    setOpen(false);
  };

  return (
    <>
      <Stack direction="row" sx={{ alignItems: 'center' }}>
        <IconButton
          aria-label={t('player.sleep.title')}
          color={isActive ? 'primary' : undefined}
          onClick={() => setOpen(true)}
          title={t('player.sleep.title')}
        >
          {isActive ? <BedtimeIcon /> : <BedtimeOutlinedIcon />}
        </IconButton>
        {running &&
          <Typography color="primary" variant="body2">
            <Countdown resetKey={running.remaining_seconds} seconds={running.remaining_seconds} />
          </Typography>
        }
        {!running && stopAfterCurrent &&
          <Typography color="primary" variant="body2">{t(`player.sleep.end.${kind}`)}</Typography>
        }
      </Stack>
      <Dialog fullWidth maxWidth="xs" onClose={() => setOpen(false)} open={open}>
        <DialogTitle>{t('player.sleep.title')}</DialogTitle>
        <DialogContent>
          <Stack spacing={1}>
            {kind !== 'radio' &&
              <Button onClick={startEndOfEntry} variant={stopAfterCurrent ? 'contained' : 'outlined'}>
                {t(`player.sleep.end-of.${kind}`)}
              </Button>
            }
            {MINUTES.map((minutes) => (
              <Button key={minutes} onClick={() => startMinutes(minutes)} variant="outlined">
                {t('player.sleep.minutes', { count: minutes })}
              </Button>
            ))}
            <FormControlLabel
              control={<Switch checked={fade} onChange={(event) => changeFade(event.target.checked)} />}
              label={t('player.sleep.fade')}
            />
            <Divider />
            <TextField
              helperText={t('player.sleep.every-start-help')}
              label={t('player.sleep.every-start')}
              onChange={(event) => saveEveryStart(Number(event.target.value), fade)}
              select
              size="small"
              value={everyStart}
            >
              <MenuItem value={0}>{t('player.sleep.every-start-off')}</MenuItem>
              {[...new Set([...MINUTES, everyStart])].filter(Boolean).sort((a, b) => a - b).map((minutes) => (
                <MenuItem key={minutes} value={minutes}>{t('player.sleep.after', { count: minutes })}</MenuItem>
              ))}
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          {isActive &&
            <Button color="error" onClick={() => cancelAll().then(() => setOpen(false))}>
              {t('player.sleep.off')}
            </Button>
          }
          <Button onClick={() => setOpen(false)}>{t('general.buttons.close')}</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default SleepTimer;
