import { useContext } from 'react';

import Grid from '@mui/material/Grid';

import Cover from './cover';
import Controls from './controls';
import PlayerActions from './actions';
import UnknownCard from './unknown-card';
import Display from './display';
import SetupNotice from '../general/setup-notice';
import TimeLimitNotice from './time-limit-notice';
import SeekBar from './seekbar';
import Volume from './volume';
import useCoverImage from './use-cover-image';

import PlayerContext from '../../context/player/context';
import { PLAYER_STATUS_TOPIC } from '../../config';

const Player = () => {
  const { state: { [PLAYER_STATUS_TOPIC]: playerstatus } } = useContext(PlayerContext);
  const { backgroundImage, coverImage } = useCoverImage(playerstatus);

  return (
    <Grid
      container
      id="player"
      sx={{
        backgroundImage,
        backgroundPosition: 'center',
      }}
    >
      <Grid
        container
        data-testid="player-backdrop"
        size={12}
        sx={{
          paddingTop: '30px',
          paddingLeft: '30px',
          paddingRight: '30px',
          minHeight: 'calc(100vh - 64px - 10px)',
          backdropFilter: 'blur(25px)',
        }}
      >
        <Grid size={{ xs: 12, sm: 5 }}>
          <Cover coverImage={coverImage} />
        </Grid>
        <Grid size={{ xs: 12, sm: 7 }}>
          <SetupNotice />
          <TimeLimitNotice />
          <Display />
          <SeekBar />
          <Controls />
          <PlayerActions />
          <UnknownCard context={playerstatus?.context} />
          <Volume />
        </Grid>
      </Grid>
    </Grid>
  );
};

export default Player;
