import { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { omit } from 'ramda';
import { useTranslation } from 'react-i18next';

import { Alert, Button } from '@mui/material';

import PubSubContext from '../../context/pubsub/context';
import { CARD_DETECTED_TOPIC } from '../../config';
import { buildActionData, findActionByCommand, findCommandByCardAction } from '../Cards/utils';

// A card that is not registered yet was placed: offer to register it, with what is playing.
const UnknownCard = ({ context }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { state: { [CARD_DETECTED_TOPIC]: detected } = {}, setState } = useContext(PubSubContext);

  if (!detected || detected.registered || detected.learned) return null;

  const dismiss = () => setState((state) => omit([CARD_DETECTED_TOPIC], state));

  const register = () => {
    const command = context?.action ? findCommandByCardAction(context.action, context.args) : undefined;
    const actionData = command
      ? buildActionData(findActionByCommand(command), command, context.args || {})
      : {};
    dismiss();
    navigate('/cards/register', { state: { registerCard: { cardId: detected.card_id, actionData } } });
  };

  return (
    <Alert
      action={<Button color="inherit" onClick={register} size="small">{t('player.card.learn')}</Button>}
      onClose={dismiss}
      severity="info"
      sx={{ marginTop: 1, width: '100%' }}
    >
      {t('player.card.unknown', { card: detected.card_id })}
    </Alert>
  );
};

export default UnknownCard;
