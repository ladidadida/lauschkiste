import { useContext, useEffect } from 'react';

import { KIOSK_TOPIC } from '../../config';
import PubSubContext from '../../context/pubsub/context';
import { isKiosk } from './kiosk';

// The screen on the box shows the kiosk app as soon as the kiosk is switched on, also from the normal web app.
const KioskRedirect = () => {
  const { state: { [KIOSK_TOPIC]: kiosk } = {} } = useContext(PubSubContext);
  useEffect(() => {
    if (kiosk?.enabled && isKiosk()) window.location.replace('/kiosk/');
  }, [kiosk]);
  return null;
};

export default KioskRedirect;
