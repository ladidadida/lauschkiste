import { memo, useContext, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import PlayCircleFilledRoundedIcon from '@mui/icons-material/PlayCircleFilledRounded';
import PauseCircleFilledRoundedIcon from '@mui/icons-material/PauseCircleFilledRounded';
import SkipPreviousRoundedIcon from '@mui/icons-material/SkipPreviousRounded';
import SkipNextRoundedIcon from '@mui/icons-material/SkipNextRounded';
import ShuffleRoundedIcon from '@mui/icons-material/ShuffleRounded';
import RepeatRoundedIcon from '@mui/icons-material/RepeatRounded';
import RepeatOneRoundedIcon from '@mui/icons-material/RepeatOneRounded';
import Forward30RoundedIcon from '@mui/icons-material/Forward30Rounded';
import Replay30RoundedIcon from '@mui/icons-material/Replay30Rounded';

import PlayerContext from '../../context/player/context';
import request from '../../utils/request';
import { PLAYER_STATUS_TOPIC } from '../../config';
import { contentKind } from './playback-context';

const SKIP_SECONDS = 30;

const Controls = () => {
  const { t } = useTranslation();
  const {
    state,
    setState,
  } = useContext(PlayerContext);

  const {
    isPlaying,
    [PLAYER_STATUS_TOPIC]: playerstatus,
    isShuffle,
    isRepeat,
    isSingle,
    songIsScheduled
  } = state;

  const toggleShuffle = () => {
    request('shuffle', { option: 'toggle' });
  }

  const toggleRepeat = () => {
    request('repeat', { option: 'toggle' });
  }

  useEffect(() => {
    setState(currentState => ({
      ...currentState,
      isPlaying: playerstatus?.state === 'play',
      songIsScheduled: playerstatus?.position != null,
      isShuffle: Boolean(playerstatus?.random),
      isRepeat: Boolean(playerstatus?.repeat),
      isSingle: Boolean(playerstatus?.single),
    }));
  }, [playerstatus, setState]);

  const iconStyles = { padding: '7px' };
  const kind = contentKind(playerstatus?.context);
  const isMusic = kind === 'music';
  const isSpoken = kind === 'audiobook' || kind === 'podcast';
  const hasTracks = kind !== 'radio' && (isMusic || (playerstatus?.playlist_length || 0) > 1);

  const skip = (seconds) => {
    const elapsed = playerstatus?.elapsed || 0;
    const duration = playerstatus?.duration || Infinity;
    request('seek', { position: Math.max(0, Math.min(elapsed + seconds, duration - 1)).toFixed(3) });
  };

  const labelShuffle = () => (
    isShuffle
      ? t('player.controls.shuffle.disable')
      : t('player.controls.shuffle.enable')
  );

  const labelRepeat = () => {
    if (!isRepeat) return t('player.controls.repeat.enable');
    if (isRepeat && !isSingle) return t('player.controls.repeat.enable-single');
    if (isRepeat && isSingle) return t('player.controls.repeat.disable');
  };

  return (
    <Grid
      container
      sx={{
        alignItems: 'center',
        flexWrap: 'nowrap',
        justifyContent: 'space-evenly',
      }}
    >

      {isMusic &&
      <IconButton
        aria-label={labelShuffle()}
        color={isShuffle ? 'primary' : undefined}
        onClick={toggleShuffle}
        size="large"
        sx={iconStyles}
        title={labelShuffle()}
      >
        <ShuffleRoundedIcon style={{ fontSize: 22 }} />
      </IconButton>
      }

      {isSpoken &&
        <IconButton
          aria-label={t('player.controls.back-30')}
          disabled={!songIsScheduled}
          onClick={() => skip(-SKIP_SECONDS)}
          size="large"
          sx={iconStyles}
          title={t('player.controls.back-30')}
        >
          <Replay30RoundedIcon style={{ fontSize: 28 }} />
        </IconButton>
      }

      {hasTracks &&
      <IconButton
        aria-label={t('player.controls.prev_song')}
        disabled={!songIsScheduled}
        onClick={() => request('prev_song')}
        size="large"
        sx={iconStyles}
        title={t('player.controls.prev_song')}
      >
        <SkipPreviousRoundedIcon style={{ fontSize: 35 }} />
      </IconButton>
      }

      {!isPlaying &&
        <IconButton
          aria-label={t('player.controls.play')}
          onClick={() => request('play')}
          disabled={!songIsScheduled}
          size="large"
          sx={iconStyles}
          title={t('player.controls.play')}
        >
          <PlayCircleFilledRoundedIcon style={{ fontSize: 75 }} />
        </IconButton>
      }
      {isPlaying &&
        <IconButton
          aria-label={t('player.controls.pause')}
          onClick={() => request('pause')}
          size="large"
          sx={iconStyles}
          title={t('player.controls.pause')}
        >
          <PauseCircleFilledRoundedIcon style={{ fontSize: 75 }} />
        </IconButton>
      }

      {hasTracks &&
      <IconButton
        aria-label={t('player.controls.next_song')}
        disabled={!songIsScheduled}
        onClick={() => request('next_song')}
        size="large"
        sx={iconStyles}
        title={t('player.controls.next_song')}
      >
        <SkipNextRoundedIcon style={{ fontSize: 35 }} />
      </IconButton>
      }

      {isSpoken &&
        <IconButton
          aria-label={t('player.controls.forward-30')}
          disabled={!songIsScheduled}
          onClick={() => skip(SKIP_SECONDS)}
          size="large"
          sx={iconStyles}
          title={t('player.controls.forward-30')}
        >
          <Forward30RoundedIcon style={{ fontSize: 28 }} />
        </IconButton>
      }

      {isMusic &&
      <IconButton
        aria-label={labelRepeat()}
        color={isRepeat ? 'primary' : undefined}
        onClick={toggleRepeat}
        size="large"
        sx={iconStyles}
        title={labelRepeat()}
      >
        {
          !isSingle &&
          <RepeatRoundedIcon style={{ fontSize: 22 }} />
        }
        {
          isSingle &&
          <RepeatOneRoundedIcon style={{ fontSize: 22 }} />
        }
      </IconButton>
      }

    </Grid>
  );
};

export default memo(Controls);
