import { useId } from 'react';
import { useTranslation } from 'react-i18next';

import {
  Box,
  FormControl,
  FormHelperText,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from '@mui/material';

import { useActionCatalog } from '../../../utils/available-actions';
import Field from './field';

const NONE = '__none__';

// An action entry ({ action, args }): pick the action, then fill in its arguments.
const ActionField = ({ help, label, nullable, onChange, value }) => {
  const { t } = useTranslation();
  const id = useId();
  const catalog = useActionCatalog();
  const selected = catalog.find(({ id }) => id === value?.action);
  const known = !value?.action || selected || !catalog.length;
  const argsSchema = selected?.args;

  return (
    <Box>
      <FormControl fullWidth size="small">
        <InputLabel id={`${id}-label`}>{label}</InputLabel>
        <Select
          label={label}
          labelId={`${id}-label`}
          onChange={(event) => onChange(event.target.value === NONE ? null : { action: event.target.value, args: {} })}
          value={value?.action || NONE}
        >
          <MenuItem value={NONE}>{nullable ? t('settings.form.no-action') : t('settings.form.choose-action')}</MenuItem>
          {!known && <MenuItem value={value.action}>{t('settings.form.unknown-action', { action: value.action })}</MenuItem>}
          {catalog.map(({ id, description }) => (
            <MenuItem key={id} value={id}>
              <Stack>
                <Typography variant="body2">{id}</Typography>
                {description && <Typography color="text.secondary" variant="caption">{description}</Typography>}
              </Stack>
            </MenuItem>
          ))}
        </Select>
        {help && <FormHelperText>{help}</FormHelperText>}
      </FormControl>
      {argsSchema && Object.keys(argsSchema.properties || {}).length > 0 &&
        <Stack spacing={2} sx={{ borderLeft: 2, borderColor: 'divider', marginTop: 2, paddingLeft: 2 }}>
          {Object.entries(argsSchema.properties).map(([key, property]) => (
            <Field
              key={key}
              onChange={(next) => onChange({ ...value, args: { ...(value?.args || {}), [key]: next } })}
              path={[key]}
              root={argsSchema}
              schema={property}
              value={value?.args?.[key] ?? property.default}
            />
          ))}
        </Stack>
      }
    </Box>
  );
};

export default ActionField;
