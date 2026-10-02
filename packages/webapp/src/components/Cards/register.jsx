import { useContext, useEffect, useState } from 'react';
import { omit } from 'ramda';
import { useTranslation } from 'react-i18next';

import PubSubContext from '../../context/pubsub/context';
import { CARD_DETECTED_TOPIC } from '../../config';
import CardsForm from './form';
import request from '../../utils/request';
import { useLocation } from 'react-router-dom';

const CardsRegister = () => {
  const { t } = useTranslation();
  const {
    state: { [CARD_DETECTED_TOPIC]: detectedCard },
    setState
  } = useContext(PubSubContext);
  const { state: locationState } = useLocation();
  const { registerCard } = locationState || {};

  const [cardId, setCardId] = useState(undefined);
  const [actionData, setActionData] = useState(registerCard?.actionData || {});

  useEffect(() => {
    setState(state => (omit([CARD_DETECTED_TOPIC], state)));
  }, [setState]);

  // While this page is open, a placed card is only reported, its action doesn't run
  useEffect(() => {
    request('rfidLearn', { seconds: 600 });
    return () => {
      request('rfidStopLearning');
    };
  }, []);

  useEffect(() => {
    setCardId(detectedCard?.card_id || registerCard?.cardId);
  }, [registerCard, detectedCard])

  return (
    <CardsForm
      title={t('cards.register.register-card')}
      cardId={cardId}
      actionData={actionData}
      setActionData={setActionData}
    />
  );
};

export default CardsRegister;
