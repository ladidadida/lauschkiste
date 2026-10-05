import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { Alert, Box, Link, Stack } from '@mui/material';

import TerminalIcon from '@mui/icons-material/Terminal';

// Settings of the operating system are made with lauschctl on the box: what, how, and where the help explains it.
const CliHint = ({ commands, section, text }) => {
  const { t } = useTranslation();
  return (
    <Alert icon={<TerminalIcon fontSize="inherit" />} severity="info" sx={{ width: '100%' }}>
      <Stack spacing={1}>
        <span>{text}</span>
        {commands.map((command) => (
          <Box component="code" key={command}
            sx={{ bgcolor: 'action.hover', borderRadius: 0.5, display: 'block', fontSize: '0.85rem', px: 1, py: 0.5 }}>
            {command}
          </Box>
        ))}
        <Link component={RouterLink} to={`/help/lauschctl${section ? `?section=${section}` : ''}`}>
          {t('settings.cli.more')}
        </Link>
      </Stack>
    </Alert>
  );
};

export default CliHint;
