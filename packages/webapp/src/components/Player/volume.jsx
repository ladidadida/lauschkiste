import { useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import Slider from '@mui/material/Slider';
import VolumeDownIcon from '@mui/icons-material/VolumeDown';
import VolumeMuteIcon from '@mui/icons-material/VolumeMute';
import VolumeOffIcon from '@mui/icons-material/VolumeOff';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import { useTheme } from '@mui/material/styles';

import PubSubContext from '../../context/pubsub/context';
import request from '../../utils/request';
import { VOLUME_LEVEL_TOPIC } from '../../config';

const Volume = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  const { state } = useContext(PubSubContext);
  const { [VOLUME_LEVEL_TOPIC]: { volume, mute, soft_max_volume } = {} } = state;

  const [isChangingVolume, setIsChangingVolume] = useState(false);
  const [_volume, setVolume] = useState(0);
  const [volumeMute, setVolumeMute] = useState(false);
  const [maxVolume, setMaxVolume] = useState(100);
  const [volumeStep] = useState(1);

  const toggleVolumeMute = () => {
    setVolumeMute(!volumeMute);
    request('toggleMuteVolume', { mute: !volumeMute });
  };

  const updateVolume = (event, newVolume) => {
    const volume = Math.min(newVolume, maxVolume);
    setVolume(volume);
    setVolumeMute(false);
    request('setVolume', { volume });
    // Delay the next command to avoid jumping slide control
    setTimeout(() => setIsChangingVolume(false), 500);
  }

  const handleVolumeChange = (event, newVolume) => {
    setIsChangingVolume(true);
    if (newVolume <= maxVolume) {
      setVolume(newVolume);
    }
  }

  useEffect(() => {
    // Don't overwrite the slider while it is being dragged
    if (volume !== undefined && !isChangingVolume) {
      setVolume(volume);
      setVolumeMute(!!mute);
      setMaxVolume(soft_max_volume);
    }
  }, [isChangingVolume, volume, mute, soft_max_volume]);

  useEffect(() => {
    const fetchVolume = async () => {
      const { result } = await request('getVolume');
      if (result) {
        setVolume(result.volume);
        setVolumeMute(result.mute);
        setMaxVolume(result.soft_max_volume);
      }
    };

    fetchVolume();
  }, []);

  const labelIcon = () => (
    volumeMute
      ? t('player.volume.unmute')
      : t('player.volume.mute')
  );

  return (
    <Grid
      container
      sx={{ alignItems: 'center', width: '100%' }}
    >
      <Grid sx={{ marginRight: theme.spacing(1) }}>
        <IconButton
          aria-label={labelIcon()}
          onClick={toggleVolumeMute}
          title={labelIcon()}
        >
          {volumeMute && <VolumeOffIcon />}
          {!volumeMute && _volume === 0 && <VolumeMuteIcon />}
          {!volumeMute && _volume > 0 && _volume < 50 && <VolumeDownIcon />}
          {!volumeMute && _volume >= 50 && <VolumeUpIcon />}
        </IconButton>
      </Grid>
      <Grid size="grow" sx={{ marginTop: theme.spacing(1) }}>
        <Slider
          aria-labelledby={t('player.volume.slider')}
          onChange={handleVolumeChange}
          onChangeCommitted={updateVolume}
          marks={[ { value: maxVolume } ]}
          step={volumeStep}
          value={_volume}
          valueLabelDisplay="auto"
        />
      </Grid>
    </Grid>
  );
}

export default Volume;
