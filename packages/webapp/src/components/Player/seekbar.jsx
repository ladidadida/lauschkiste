import { useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import PlayerContext from '../../context/player/context';
import { PLAYER_STATUS_TOPIC } from '../../config';
import { contentKind } from './playback-context';
import {
  progressToTime,
  timeToProgress,
  toHHMMSS,
} from '../../utils/utils';

import Grid from '@mui/material/Grid';
import Slider from '@mui/material/Slider';
import Typography from '@mui/material/Typography';

import request from '../../utils/request';

const SeekBar = () => {
  const { t } = useTranslation();
  const { state } = useContext(PlayerContext);
  const { [PLAYER_STATUS_TOPIC]: playerstatus } = state;

  const [isSeeking, setIsSeeking] = useState(false);
  const [progress, setProgress] = useState(0);
  const [timeElapsed, setTimeElapsed] = useState(playerstatus?.elapsed || 0);
  const timeTotal = playerstatus?.duration || 0;

  const updateTimeAndProgress = (newTime) => {
    setTimeElapsed(newTime);
    setProgress(timeToProgress(timeTotal, newTime));
  };

  // Handle seek events when sliding the progress bar
  const handleSeekToPosition = (event, newPosition) => {
    setIsSeeking(true);
    updateTimeAndProgress(progressToTime(timeTotal, newPosition));
  };

  // Only send commend to backend when user committed to new position
  // We don't send it while seeking (too many useless requests)
  const playFromNewTime = () => {
    request('seek', { position: timeElapsed.toFixed(3) });
    setIsSeeking(false);
  };

  useEffect(() => {
    // Avoid updating time and progress when user is seeking to new
    // song position
    if (!isSeeking) {
      const elapsed = playerstatus?.elapsed || 0;
      setTimeElapsed(elapsed);
      setProgress(timeToProgress(timeTotal, elapsed));
    }
  }, [isSeeking, playerstatus?.elapsed, timeTotal]);

  if (contentKind(playerstatus?.context) === 'radio') return null;

  return <>
    <Grid container>
      <Grid size="grow">
        <Slider
          aria-labelledby={t('player.seekbar.song-position')}
          disabled={!timeTotal}
          onChange={handleSeekToPosition}
          onChangeCommitted={playFromNewTime}
          size="small"
          value={progress || 0}
        />
      </Grid>
    </Grid>
    <Grid
      container
      sx={{
        alignItems: 'center',
        justifyContent: 'space-between',
        marginTop: '-10px',
      }}
    >
      <Grid>
        <Typography color="textSecondary">
          {toHHMMSS(parseInt(timeElapsed))}
        </Typography>
      </Grid>
      <Grid>
        <Typography color="textSecondary">
          {toHHMMSS(parseInt(timeTotal))}
        </Typography>
      </Grid>
    </Grid>
  </>;
};

export default SeekBar;
