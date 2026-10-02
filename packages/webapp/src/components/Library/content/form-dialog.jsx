import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
} from '@mui/material';

import { requestErrorMessage } from '../../../utils/request';

// A dialog with text `fields` ({ name, label, required, type, helperText }); `onSubmit(values)`
// returns the request result ({ error } on failure).
const FormDialog = ({
  confirmLabel,
  fields,
  initialValues = {},
  onClose,
  onSubmit,
  onSaved,
  open,
  title,
}) => {
  const { t } = useTranslation();
  const [values, setValues] = useState(initialValues);
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setValues(initialValues);
      setError('');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const missing = fields.some(({ name, required }) => required && !String(values[name] || '').trim());

  const submit = async (event) => {
    event.preventDefault();
    if (missing) return;
    setIsSaving(true);
    setError('');
    const trimmed = Object.fromEntries(
      fields.map(({ name }) => [name, String(values[name] || '').trim()]),
    );
    const { result, error: requestError } = await onSubmit(trimmed);
    setIsSaving(false);
    if (requestError) {
      setError(requestErrorMessage(requestError) || t('library.content.save-error'));
      return;
    }
    onSaved?.(result);
  };

  const close = () => {
    if (!isSaving) onClose();
  };

  return (
    <Dialog fullWidth maxWidth="sm" onClose={close} open={open}>
      <form onSubmit={submit}>
        <DialogTitle>{title}</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ marginBottom: 2 }}>{error}</Alert>}
          {fields.map(({ name, label, required, type = 'text', helperText }, index) => (
            <TextField
              autoFocus={index === 0}
              disabled={isSaving}
              fullWidth
              helperText={helperText}
              key={name}
              label={label}
              margin="dense"
              name={name}
              onChange={(event) => setValues({ ...values, [name]: event.target.value })}
              required={required}
              type={type}
              value={values[name] || ''}
            />
          ))}
        </DialogContent>
        <DialogActions>
          <Button disabled={isSaving} onClick={close} sx={{ minHeight: 44 }}>
            {t('general.buttons.cancel')}
          </Button>
          <Button disabled={isSaving || missing} sx={{ minHeight: 44 }} type="submit" variant="contained">
            {confirmLabel || t('general.buttons.save')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default FormDialog;
