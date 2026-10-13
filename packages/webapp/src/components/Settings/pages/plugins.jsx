import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  IconButton,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Stack,
  Switch,
  TextField,
  Typography,
} from '@mui/material';

import SettingsIcon from '@mui/icons-material/Settings';

import request from '../../../utils/request';
import { pluginName } from '../../../utils/plugin-name';
import ModuleSettings from '../form/module-settings';
import { useRestart } from '../restart';
import SettingsPage from './page';

const blockedText = (t, blocked) => {
  if (blocked.taken_by) return t('settings.plugins.blocked-device', { name: pluginName(t, blocked.taken_by) });
  if (blocked.incompatible) return blocked.incompatible;
  return t('settings.plugins.blocked-needs', {
    needs: blocked.missing.map((need) => t(`settings.plugins.capabilities.${need}`, { defaultValue: need })).join(', '),
  });
};

const GROUPS = ['hardware', 'feature'];

const PluginRow = ({ plugin, withSettings, installing, toggle, install }) => {
  const { t } = useTranslation();
  return (
    <ListItem
      disableGutters
      secondaryAction={
        <Stack direction="row" sx={{ alignItems: 'center' }}>
          {withSettings.has(plugin.name) &&
            <IconButton
              aria-label={t('settings.plugins.settings', { name: plugin.name })}
              component={Link}
              nativeButton={false}
              to={`/settings/plugins/${plugin.name}`}
            >
              <SettingsIcon />
            </IconButton>
          }
          <Switch
            checked={plugin.enabled}
            disabled={!plugin.enabled && (!plugin.package || Boolean(plugin.blocked))}
            onChange={(event) => toggle(plugin.name, event.target.checked)}
            slotProps={{ input: { 'aria-label': t('settings.plugins.enable', { name: plugin.name }) } }}
          />
        </Stack>
      }
      sx={{ paddingRight: 12 }}
    >
      <ListItemText
        primary={
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
            <span>{pluginName(t, plugin.name, plugin.title)}</span>
            {plugin.running && <Chip color="success" label={t('settings.plugins.running')} size="small" />}
            {plugin.enabled && !plugin.running &&
              <Chip color="warning" label={t('settings.plugins.not-running')} size="small" />}
            {plugin.detected && !plugin.enabled &&
              <Chip color="info" label={t('settings.plugins.detected', { model: plugin.detected })} size="small" />}
          </Stack>
        }
        secondary={
          <>
            <span>{t(`settings.plugins.descriptions.${plugin.name}`, { defaultValue: plugin.summary })}</span>
            {plugin.blocked && !plugin.enabled &&
              <Alert component="span" severity="info" sx={{ display: 'flex', marginTop: 1 }}>
                {blockedText(t, plugin.blocked)}
              </Alert>
            }
            {plugin.problem && plugin.enabled &&
              <Alert component="span" severity="error" sx={{ display: 'flex', marginTop: 1 }}>
                {plugin.problem}
              </Alert>
            }
            {plugin.enabled && (plugin.missing_extras.length > 0 || plugin.installing) &&
              <Alert
                action={
                  <Button color="inherit" disabled={installing} onClick={() => install(plugin.name)} size="small">
                    {plugin.installing ? <CircularProgress color="inherit" size={16} />
                      : t('settings.plugins.install')}
                  </Button>
                }
                component="span"
                severity="info"
                sx={{ display: 'flex', marginTop: 1 }}
              >
                {plugin.installing ? t('settings.plugins.installing') : t('settings.plugins.missing-extras')}
              </Alert>
            }
            {plugin.install_error &&
              <Alert component="span" severity="error" sx={{ display: 'flex', marginTop: 1 }}>
                {t('settings.plugins.install-error', { error: plugin.install_error })}
              </Alert>
            }
          </>
        }
        slotProps={{ secondary: { component: 'div' } }}
      />
    </ListItem>
  );
};

const DeviceChoice = ({ devices, withSettings, change }) => {
  const { t } = useTranslation();
  const current = devices.find((device) => device.enabled);
  const label = (device) => `${pluginName(t, device.name, device.title)}${device.detected
    ? ` (${t('settings.plugins.detected', { model: device.detected })})` : ''}`;
  return (
    <Card sx={{ marginBottom: 2 }}>
      <CardContent>
        <Typography variant="h6">{t('settings.plugins.device-title')}</Typography>
        <Typography color="text.secondary" sx={{ marginBottom: 2 }} variant="body2">
          {t('settings.plugins.device-help')}
        </Typography>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
          <TextField
            fullWidth
            label={t('settings.plugins.device-label')}
            onChange={(event) => change(event.target.value)}
            select
            size="small"
            value={current ? current.name : ''}
          >
            <MenuItem value="">{t('settings.plugins.device-none')}</MenuItem>
            {devices.map((device) => (
              <MenuItem
                disabled={!device.enabled && (!device.package || Boolean(device.blocked?.incompatible))}
                key={device.name}
                value={device.name}
              >
                {label(device)}
              </MenuItem>
            ))}
          </TextField>
          {current && withSettings.has(current.name) &&
            <IconButton
              aria-label={t('settings.plugins.settings', { name: current.name })}
              component={Link}
              nativeButton={false}
              to={`/settings/plugins/${current.name}`}
            >
              <SettingsIcon />
            </IconButton>
          }
        </Stack>
        {current?.problem &&
          <Alert severity="error" sx={{ marginTop: 1 }}>{current.problem}</Alert>}
        {devices.filter((device) => !device.enabled && device.blocked?.incompatible).map((device) => (
          <Typography color="text.secondary" key={device.name} sx={{ marginTop: 1 }} variant="body2">
            {pluginName(t, device.name, device.title)}: {device.blocked.incompatible}
          </Typography>
        ))}
      </CardContent>
    </Card>
  );
};

const PluginsSettings = () => {
  const { t } = useTranslation();
  const { refresh } = useRestart();
  const [plugins, setPlugins] = useState(null);
  const [withSettings, setWithSettings] = useState(new Set());

  const load = useCallback(async () => {
    const [{ result }, { result: settings }] = await Promise.all([
      request('pluginsList'), request('moduleSettingsList'),
    ]);
    setPlugins(result || []);
    setWithSettings(new Set((settings || []).filter(({ kind }) => kind === 'plugin').map(({ name }) => name)));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const installing = (plugins || []).some((plugin) => plugin.installing);
  useEffect(() => {
    if (!installing) return undefined;
    const timer = setInterval(load, 3000);
    return () => clearInterval(timer);
  }, [installing, load]);

  useEffect(() => {
    if (!installing) refresh();
  }, [installing, refresh]);

  const install = async (name) => {
    await request('installPluginExtras', { name });
    load();
  };

  const toggle = async (name, enabled) => {
    await request('setPluginEnabled', { name, enabled });
    await load();
    refresh();
  };

  const changeDevice = async (name) => {
    const current = devices.find((device) => device.enabled);
    if (current && current.name !== name) await request('setPluginEnabled', { name: current.name, enabled: false });
    if (name) await request('setPluginEnabled', { name, enabled: true });
    await load();
    refresh();
  };

  const devices = (plugins || []).filter(({ kind }) => kind === 'device');

  return (
    <SettingsPage title={t('settings.sections.plugins.title')}>
      {!plugins && <CircularProgress />}
      {devices.length > 0 && <DeviceChoice change={changeDevice} devices={devices} withSettings={withSettings} />}
      {plugins && plugins.length === 0 && <Typography sx={{ marginTop: 2 }}>{t('settings.plugins.none')}</Typography>}
      {GROUPS.map((group) => {
        const members = (plugins || []).filter(({ kind }) => (kind || 'feature') === group);
        if (members.length === 0) return null;
        return (
          <Card key={group} sx={{ marginBottom: 2 }}>
            <CardContent>
              <Typography variant="h6">{t(`settings.plugins.groups.${group}.title`)}</Typography>
              <Typography color="text.secondary" variant="body2">{t(`settings.plugins.groups.${group}.help`)}</Typography>
              <List>
                {members.map((plugin) => (
                  <PluginRow
                    installing={installing}
                    install={install}
                    key={plugin.name}
                    plugin={plugin}
                    toggle={toggle}
                    withSettings={withSettings}
                  />
                ))}
              </List>
            </CardContent>
          </Card>
        );
      })}
    </SettingsPage>
  );
};

const PluginSettings = () => {
  const { t } = useTranslation();
  const { name } = useParams();
  return (
    <SettingsPage title={pluginName(t, name)}>
      <ModuleSettings module={name} title={t('settings.plugins.settings-title')} />
    </SettingsPage>
  );
};

export { PluginSettings, PluginsSettings };
