import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Button, Menu, MenuItem } from '@mui/material';

import request from '../../../utils/request';

const SPEEDS = [0.75, 0.9, 1, 1.1, 1.25, 1.5];

const format = (speed) => `${Number(speed).toLocaleString(undefined, { maximumFractionDigits: 2 })}×`;

// Playback speed of audiobooks and podcasts.
const Speed = ({ speed = 1 }) => {
  const { t } = useTranslation();
  const [anchor, setAnchor] = useState(null);

  return (
    <>
      <Button
        aria-label={t('player.speed.title')}
        color={Math.abs(speed - 1) > 0.01 ? 'primary' : 'inherit'}
        onClick={(event) => setAnchor(event.currentTarget)}
        size="small"
        title={t('player.speed.title')}
      >
        {format(speed)}
      </Button>
      <Menu anchorEl={anchor} onClose={() => setAnchor(null)} open={Boolean(anchor)}>
        {SPEEDS.map((value) => (
          <MenuItem
            key={value}
            onClick={() => {
              request('setSpeed', { speed: value });
              setAnchor(null);
            }}
            selected={Math.abs(value - speed) < 0.01}
          >
            {format(value)}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
};

export default Speed;
