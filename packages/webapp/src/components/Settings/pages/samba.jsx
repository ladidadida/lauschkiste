import { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import {
  Alert,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Divider,
  FormControlLabel,
  Link,
  Stack,
  Switch,
  TextField,
  Typography,
} from '@mui/material';

import request, { requestErrorMessage } from '../../../utils/request';
import CliHint from '../cli-hint';

const MIN_PASSWORD = 8;

// The Samba share of the library, managed through the samba plugin.
const SambaSettings = () => {
  const { t } = useTranslation();
  const [status, setStatus] = useState(undefined);
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    request('sambaStatus').then(({ result }) => setStatus(result || null));
  }, []);

  const run = async (command, args, success) => {
    setBusy(true);
    setMessage(null);
    const { result, error } = await request(command, args);
    setBusy(false);
    if (error) {
      setMessage({ severity: 'error', text: requestErrorMessage(error) || t('settings.samba.error') });
      return;
    }
    setStatus(result);
    setMessage(success ? { severity: 'success', text: success } : null);
  };

  const body = () => {
    if (status === undefined) return <CircularProgress />;
    if (status === null) {
      return (
        <Stack spacing={2}>
          <Typography variant="body2">{t('settings.samba.plugin-off')}</Typography>
          <Button component={RouterLink} sx={{ alignSelf: 'flex-start' }} to="/settings/plugins" variant="outlined">
            {t('settings.sections.plugins.title')}
          </Button>
        </Stack>
      );
    }
    if (!status.installed) {
      return <CliHint commands={['lauschctl setup samba']} section="samba" text={t('settings.samba.not-installed')} />;
    }
    return (
      <Stack spacing={2}>
        <FormControlLabel
          control={<Switch checked={status.shared} disabled={busy}
            onChange={(event) => run('sambaShare', { enabled: event.target.checked })} />}
          label={t('settings.samba.share')}
        />
        {status.shared && status.address &&
          <Alert icon={false} severity="success">
            <Typography sx={{ fontWeight: 600 }} variant="body2">{t('settings.samba.login')}</Typography>
            <Typography variant="body2">{t('settings.samba.login-user', { user: status.user })}</Typography>
            <Typography variant="body2">{t('settings.samba.login-password')}</Typography>
            <Typography variant="body2">
              {t('settings.samba.login-windows', { address: status.address.replace(/^smb:/, '').replaceAll('/', '\\') })}
            </Typography>
            <Typography variant="body2">{t('settings.samba.login-mac', { address: status.address })}</Typography>
            <Link component={RouterLink} to="/help/library?section=samba">{t('settings.cli.more')}</Link>
          </Alert>
        }
        {status.outdated && <Alert severity="info">{t('settings.samba.outdated')}</Alert>}
        <Typography variant="body2">
          {status.has_password ? t('settings.samba.password-set', { user: status.user })
            : t('settings.samba.password-missing', { user: status.user })}
        </Typography>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start' }}>
          <TextField
            autoComplete="new-password"
            helperText={t('settings.samba.password-help', { count: MIN_PASSWORD })}
            label={t('settings.samba.password')}
            onChange={(event) => setPassword(event.target.value)}
            size="small"
            type="password"
            value={password}
          />
          <Button
            disabled={busy || password.length < MIN_PASSWORD}
            onClick={() => run('sambaPassword', { password }, t('settings.samba.password-saved')).then(() => setPassword(''))}
            variant="outlined"
          >
            {t('general.buttons.save')}
          </Button>
        </Stack>
        {message && <Alert severity={message.severity}>{message.text}</Alert>}
      </Stack>
    );
  };

  return (
    <Card>
      <CardHeader title={t('settings.library.share')} />
      <Divider />
      <CardContent>{body()}</CardContent>
    </Card>
  );
};

export default SambaSettings;
