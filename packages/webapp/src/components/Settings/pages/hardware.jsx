import { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import {
  Alert,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  CircularProgress,
  Collapse,
  Divider,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';

import request from '../../../utils/request';
import CliHint from '../cli-hint';
import { useRestart } from '../restart';
import SettingsPage from './page';

const usage = (users) => users.map(({ owner, purpose }) => (purpose ? `${owner}: ${purpose}` : owner)).join(', ');

const PinTable = ({ pins }) => {
  const { t } = useTranslation();
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>{t('settings.hardware.pin')}</TableCell>
          <TableCell>{t('settings.hardware.functions')}</TableCell>
          <TableCell>{t('settings.hardware.used-by')}</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {pins.map((pin) => (
          <TableRow key={pin.id} sx={pin.conflict ? { bgcolor: 'error.dark' } : undefined}>
            <TableCell>{pin.label}</TableCell>
            <TableCell>{pin.functions.filter((name) => name !== 'gpio').join(', ')}</TableCell>
            <TableCell>{usage(pin.used_by)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

// The board, pending boot changes, conflicts and the pin map.
const HardwareSettings = () => {
  const { t } = useTranslation();
  const [state, setState] = useState(undefined);
  const [showAll, setShowAll] = useState(false);
  const [enabled, setEnabled] = useState(null);
  const { refresh } = useRestart();

  const enable = async (name) => {
    const { error } = await request('setPluginEnabled', { name, enabled: true });
    if (!error) setEnabled(name);
    refresh();
  };

  useEffect(() => {
    request('hardwareState').then(({ result }) => setState(result || null));
  }, []);

  const body = () => {
    if (state === undefined) return <CircularProgress />;
    if (!state?.board) {
      return (
        <Card>
          <CardContent>
            <Typography sx={{ marginBottom: 2 }}>{t('settings.hardware.no-board')}</Typography>
            {(state?.detected || []).map(({ name, model }) => (
              <Alert
                action={enabled !== name &&
                  <Button color="inherit" onClick={() => enable(name)} size="small">{t('settings.hardware.enable-board')}</Button>
                }
                key={name}
                severity={enabled === name ? 'success' : 'info'}
                sx={{ marginBottom: 2 }}
              >
                {enabled === name ? t('settings.hardware.board-enabled')
                  : t('settings.hardware.detected', { model, name: t(`settings.plugins.names.${name}`, { defaultValue: name }) })}
              </Alert>
            ))}
            <Button component={RouterLink} to="/settings/plugins" variant="outlined">
              {t('settings.sections.plugins.title')}
            </Button>
          </CardContent>
        </Card>
      );
    }
    const used = state.pins.filter((pin) => pin.used_by.length);
    const free = state.pins.filter((pin) => !pin.used_by.length);
    return (
      <>
        <Card>
          <CardHeader subheader={state.board} title={state.model} />
          <Divider />
          <CardContent>
            <Stack spacing={1}>
              <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                {state.interfaces.filter(({ used_by: users }) => users.length).map((entry) => (
                  <Chip key={entry.id} label={`${entry.label}: ${usage(entry.used_by)}`} size="small" />
                ))}
              </Stack>
              <Button component={RouterLink} sx={{ alignSelf: 'flex-start' }}
                to={`/settings/plugins/board_${state.board}`} variant="outlined">
                {t('settings.hardware.board-settings')}
              </Button>
            </Stack>
          </CardContent>
        </Card>
        {state.boot_pending.length > 0 &&
          <CliHint commands={['lauschctl setup raspi', 'sudo reboot']} section="audio"
            text={t('settings.hardware.boot-pending', { changes: state.boot_pending.join(', ') })} />
        }
        {state.conflicts.length > 0 &&
          <Alert severity="error">{t('settings.hardware.conflicts', { pins: state.conflicts.join(', ') })}</Alert>
        }
        {state.unknown.length > 0 &&
          <Alert severity="warning">
            {t('settings.hardware.unknown', { pins: state.unknown.map((claim) => `${claim.resource} (${claim.owner})`).join(', ') })}
          </Alert>
        }
        <Card>
          <CardHeader title={t('settings.hardware.pins')} />
          <Divider />
          <CardContent>
            {used.length ? <PinTable pins={used} /> : <Typography>{t('settings.hardware.nothing-used')}</Typography>}
            <Button onClick={() => setShowAll(!showAll)} size="small" sx={{ marginTop: 1 }}>
              {showAll ? t('settings.hardware.hide-free') : t('settings.hardware.show-free', { count: free.length })}
            </Button>
            <Collapse in={showAll}><PinTable pins={free} /></Collapse>
          </CardContent>
        </Card>
      </>
    );
  };

  return <SettingsPage title={t('settings.sections.hardware.title')}>{body()}</SettingsPage>;
};

export default HardwareSettings;
