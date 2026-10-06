import { useContext } from 'react';
import { useTranslation } from 'react-i18next';

import {
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
} from '@mui/material';

import BatteryIcon from '../helpers/battery-icon';
import PubSubContext from '../../../context/pubsub/context';
import { BATTERY_TOPIC } from '../../../config';

// Shown while the battery plugin publishes readings.
const StatusBattery = () => {
  const { t } = useTranslation();
  const { state: { [BATTERY_TOPIC]: battery } } = useContext(PubSubContext);

  if (!battery) {
    return null;
  }

  return (
    <ListItem disableGutters>
      <ListItemAvatar>
        <Avatar>
          <BatteryIcon soc={battery.soc} charging={false} />
        </Avatar>
      </ListItemAvatar>
      <ListItemText
        primary={`${battery.soc}% (${(battery.voltage_mv / 1000).toFixed(2)} V)`}
        secondary={t('settings.status.battery.title')}
      />
    </ListItem>
  );
};

export default StatusBattery;
