import { useContext } from 'react';

import { Box } from '@mui/material';

import Controls from '../../components/Player/controls';
import Cover from '../../components/Player/cover';
import Display from '../../components/Player/display';
import SeekBar from '../../components/Player/seekbar';
import TimeLimitNotice from '../../components/Player/time-limit-notice';
import Volume from '../../components/Player/volume';
import useCoverImage from '../../components/Player/use-cover-image';
import PlayerContext from '../../context/player/context';
import { PLAYER_STATUS_TOPIC } from '../../config';

// What plays now: the cover next to (or above) the title, the progress, the controls and the volume.
const PlayerPage = ({ showVolume }) => {
  const { state: { [PLAYER_STATUS_TOPIC]: status } } = useContext(PlayerContext);
  const { backgroundImage, coverImage } = useCoverImage(status);

  return (
    <Box
      data-testid="kiosk-player"
      sx={{
        backgroundImage,
        backgroundPosition: 'center',
        backgroundSize: 'cover',
        minHeight: '100%',
      }}
    >
      <Box
        sx={{
          alignItems: 'center',
          backdropFilter: 'blur(25px)',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          minHeight: '100%',
          padding: 2,
          '@media (orientation: landscape)': { flexDirection: 'row' },
        }}
      >
        <Box sx={{ flex: '0 0 auto', width: { xs: '60%', sm: '40%' }, '@media (orientation: landscape)': { width: '38%' } }}>
          <Cover coverImage={coverImage} />
        </Box>
        <Box sx={{ flex: 1, minWidth: 0, width: '100%' }}>
          <TimeLimitNotice />
          <Display linkToLibrary={false} />
          <SeekBar />
          <Controls />
          {showVolume && <Volume />}
        </Box>
      </Box>
    </Box>
  );
};

export default PlayerPage;
