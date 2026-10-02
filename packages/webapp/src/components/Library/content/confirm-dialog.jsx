import { useTranslation } from 'react-i18next';

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from '@mui/material';

const ConfirmDialog = ({
  confirmLabel,
  onClose,
  onConfirm,
  open,
  text,
  title,
}) => {
  const { t } = useTranslation();

  return (
    <Dialog fullWidth maxWidth="xs" onClose={onClose} open={open}>
      <DialogTitle>{title}</DialogTitle>
      {text && <DialogContent><DialogContentText>{text}</DialogContentText></DialogContent>}
      <DialogActions>
        <Button onClick={onClose} sx={{ minHeight: 44 }}>{t('general.buttons.cancel')}</Button>
        <Button color="error" onClick={onConfirm} sx={{ minHeight: 44 }} variant="contained">
          {confirmLabel || t('general.buttons.delete')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConfirmDialog;
