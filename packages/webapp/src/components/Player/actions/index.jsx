import { useContext } from 'react';

import { Stack } from '@mui/material';

import PlayerContext from '../../../context/player/context';
import { PLAYER_STATUS_TOPIC } from '../../../config';
import { contentKind } from '../playback-context';
import CardFromPlayer from './card-from-player';
import MusicSearch from './music-search';
import SleepTimer from './sleep-timer';

const PlayerActions = () => {
  const { state: { [PLAYER_STATUS_TOPIC]: playerstatus } } = useContext(PlayerContext);
  const kind = contentKind(playerstatus?.context);

  return (
    <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-evenly', marginY: 1 }}>
      <MusicSearch />
      <CardFromPlayer context={playerstatus?.context} />
      <SleepTimer kind={kind} stopAfterCurrent={Boolean(playerstatus?.stop_after_current)} />
    </Stack>
  );
};

export default PlayerActions;
