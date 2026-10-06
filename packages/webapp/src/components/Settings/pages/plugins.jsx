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
  Stack,
  Switch,
  Typography,
} from '@mui/material';

import SettingsIcon from '@mui/icons-material/Settings';

import request from '../../../utils/request';
import ModuleSettings from '../form/module-settings';
import { useRestart } from '../restart';
import SettingsPage from './page';

const blockedText = (t, blocked) => (blocked.taken_by
  ? t('settings.plugins.blocked-board', { name: t(`settings.plugins.names.${blocked.taken_by}`, { defaultValue: blocked.taken_by }) })
  : t('settings.plugins.blocked-needs', {
    needs: blocked.missing.map((need) => t(`settings.plugins.capabilities.${need}`, { defaultValue: need })).join(', '),
  }));

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

  return (
    <SettingsPage title={t('settings.sections.plugins.title')}>
      <Card>
        <CardContent>
          <Typography color="text.secondary" variant="body2">{t('settings.plugins.help')}</Typography>
          {!plugins && <CircularProgress />}
          {plugins && plugins.length === 0 && <Typography sx={{ marginTop: 2 }}>{t('settings.plugins.none')}</Typography>}
          <List>
            {(plugins || []).map((plugin) => (
              <ListItem
                disableGutters
                key={plugin.name}
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
                      <span>{t(`settings.plugins.names.${plugin.name}`, { defaultValue: plugin.name })}</span>
                      {plugin.running && <Chip color="success" label={t('settings.plugins.running')} size="small" />}
                      {plugin.enabled && !plugin.running &&
                        <Chip color="warning" label={t('settings.plugins.not-running')} size="small" />}
                      {plugin.detected && !plugin.enabled &&
                        <Chip color="info" label={t('settings.plugins.detected', { model: plugin.detected })} size="small" />}
                    </Stack>
                  }
                  secondary={
                    <>
                      <span>{plugin.summary}</span>
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
            ))}
          </List>
        </CardContent>
      </Card>
    </SettingsPage>
  );
};

const PluginSettings = () => {
  const { t } = useTranslation();
  const { name } = useParams();
  return (
    <SettingsPage title={t(`settings.plugins.names.${name}`, { defaultValue: name })}>
      <ModuleSettings module={name} title={t('settings.plugins.settings-title')} />
    </SettingsPage>
  );
};

export { PluginSettings, PluginsSettings };
