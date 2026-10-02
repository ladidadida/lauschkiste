import { useContext, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  Alert,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  Typography,
} from '@mui/material';

import NfcIcon from '@mui/icons-material/Nfc';

import PubSubContext from '../../../context/pubsub/context';
import request, { requestErrorMessage } from '../../../utils/request';
import { CARD_DETECTED_TOPIC } from '../../../config';

const LEARN_SECONDS = 60;

// Put what is playing on the next card placed on the reader.
const CardFromPlayer = ({ context }) => {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState('waiting');
  const [card, setCard] = useState(null);
  const [error, setError] = useState('');
  const { state: { [CARD_DETECTED_TOPIC]: detected } = {} } = useContext(PubSubContext);
  const seen = useRef(null);

  const save = async (cardId) => {
    const { error: requestError } = await request('registerCard', {
      card_id: cardId, action: context.action, args: context.args || {}, overwrite: true,
    });
    if (requestError) {
      setError(requestErrorMessage(requestError) || t('player.card.error'));
      setStep('error');
      return;
    }
    setStep('done');
  };

  useEffect(() => {
    if (!open || step !== 'waiting' || !detected || detected === seen.current || !detected.learned) return;
    seen.current = detected;
    setCard(detected);
    if (detected.registered) setStep('confirm');
    else save(detected.card_id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detected, open, step]);

  const start = () => {
    seen.current = detected;
    setCard(null);
    setError('');
    setStep('waiting');
    setOpen(true);
    request('rfidLearn', { seconds: LEARN_SECONDS });
  };

  const close = () => {
    if (step === 'waiting') request('rfidStopLearning');
    setOpen(false);
  };

  return (
    <>
      <IconButton
        aria-label={t('player.card.title')}
        disabled={!context?.action}
        onClick={start}
        title={t('player.card.title')}
      >
        <NfcIcon />
      </IconButton>
      <Dialog fullWidth maxWidth="xs" onClose={close} open={open}>
        <DialogTitle>{t('player.card.title')}</DialogTitle>
        <DialogContent>
          {step === 'waiting' &&
            <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
              <CircularProgress size={28} />
              <Typography>{t('player.card.place', { title: context?.title || '' })}</Typography>
            </Stack>
          }
          {step === 'confirm' &&
            <Typography>{t('player.card.overwrite', { card: card?.card_id })}</Typography>
          }
          {step === 'done' &&
            <Alert severity="success">{t('player.card.done', { card: card?.card_id, title: context?.title || '' })}</Alert>
          }
          {step === 'error' && <Alert severity="error">{error}</Alert>}
        </DialogContent>
        <DialogActions>
          {step === 'confirm' &&
            <Button color="warning" onClick={() => save(card.card_id)} variant="contained">
              {t('player.card.overwrite-confirm')}
            </Button>
          }
          <Button onClick={close}>
            {step === 'done' ? t('general.buttons.close') : t('general.buttons.cancel')}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default CardFromPlayer;
