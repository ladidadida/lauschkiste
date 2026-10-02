import { useContext } from 'react';

import { Stack } from '@mui/material';

import PlayerContext from '../../../context/player/context';
import { PLAYER_STATUS_TOPIC } from '../../../config';
import { contentKind } from '../playback-context';
import CardFromPlayer from './card-from-player';
import MusicSearch from './music-search';
import Queue from './queue';
import SleepTimer from './sleep-timer';
import Speed from './speed';

const PlayerActions = () => {
  const { state: { [PLAYER_STATUS_TOPIC]: playerstatus } } = useContext(PlayerContext);
  const kind = contentKind(playerstatus?.context);

  return (
    <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-evenly', marginY: 1 }}>
      <MusicSearch />
      {kind !== 'radio' &&
        <Queue kind={kind} length={playerstatus?.playlist_length || 0} position={playerstatus?.position} />
      }
      {(kind === 'audiobook' || kind === 'podcast') && <Speed speed={playerstatus?.speed} />}
      <CardFromPlayer context={playerstatus?.context} />
      <SleepTimer kind={kind} stopAfterCurrent={Boolean(playerstatus?.stop_after_current)} />
    </Stack>
  );
};

export default PlayerActions;
