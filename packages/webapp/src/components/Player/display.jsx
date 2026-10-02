import { useContext } from 'react';
import { useTranslation } from 'react-i18next';

import PlayerContext from '../../context/player/context';
import { PLAYER_STATUS_TOPIC } from '../../config';

import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';

const Display = () => {
  const { t } = useTranslation();
  const { state: { [PLAYER_STATUS_TOPIC]: playerstatus } } = useContext(PlayerContext);
  const hasSong = playerstatus?.position != null;

  const dontBreak = {
    whiteSpace: 'nowrap',
    width: '100%',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  };

  return (
    <Grid container>
      <Typography sx={dontBreak} component="h5" variant="h5">
        {hasSong
          ? (playerstatus?.title || playerstatus?.name || t('player.display.unknown-title'))
          : t('player.display.no-song-in-queue')
        }
      </Typography>
      {hasSong && playerstatus?.name &&
        <Typography sx={dontBreak} variant="subtitle1" color="textSecondary">
          {playerstatus.name}
        </Typography>
      }
      {hasSong && !playerstatus?.name &&
        <Typography sx={dontBreak} variant="subtitle1" color="textSecondary">
          {playerstatus?.artist || t('player.display.unknown-artist')}
          <span style={{ marginLeft: '5px', marginRight: '5px' }}>&bull;</span>
          {playerstatus?.album || playerstatus?.file}
        </Typography>
      }
    </Grid>
  );
};

export default Display;
