import { useContext } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import Grid from '@mui/material/Grid';
import MuiLink from '@mui/material/Link';
import Typography from '@mui/material/Typography';

import PlayerContext from '../../context/player/context';
import { PLAYER_STATUS_TOPIC } from '../../config';
import { contentKind, libraryLink } from './playback-context';

const dontBreak = {
  whiteSpace: 'nowrap',
  width: '100%',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
};

// Title and subtitle for what is playing, by content type.
const lines = (status, t) => {
  const { context } = status;
  const kind = contentKind(context);
  if (kind === 'radio') {
    const station = status.name || context?.title || t('player.display.unknown-title');
    return [station, status.title !== station ? status.title : null,
      [status.genre, status.description].filter(Boolean).join(' · ')];
  }
  if (kind === 'audiobook') {
    const chapter = status.playlist_length > 1
      ? t('player.display.chapter', { chapter: status.position + 1, chapters: status.playlist_length })
      : null;
    return [context?.title || status.album || t('player.display.unknown-title'),
      [chapter, status.title].filter(Boolean).join(' · ')];
  }
  if (kind === 'podcast') {
    return [status.title || context?.title || t('player.display.unknown-title'), context?.title];
  }
  return [
    status.title || t('player.display.unknown-title'),
    [status.artist || t('player.display.unknown-artist'), status.album || status.file].filter(Boolean).join(' • '),
  ];
};

const Display = () => {
  const { t } = useTranslation();
  const { state: { [PLAYER_STATUS_TOPIC]: playerstatus } } = useContext(PlayerContext);
  const hasSong = playerstatus?.position != null;

  if (!hasSong) {
    return (
      <Grid container>
        <Typography sx={dontBreak} component="h5" variant="h5">
          {t('player.display.no-song-in-queue')}
        </Typography>
      </Grid>
    );
  }

  const [title, subtitle, extra] = lines(playerstatus, t);

  return (
    <Grid container>
      <MuiLink
        color="inherit"
        component={Link}
        sx={dontBreak}
        title={t('player.display.show-in-library')}
        to={libraryLink(playerstatus.context)}
        underline="hover"
      >
        <Typography sx={dontBreak} component="h5" variant="h5">{title}</Typography>
      </MuiLink>
      {subtitle &&
        <Typography sx={dontBreak} variant="subtitle1" color="textSecondary">{subtitle}</Typography>
      }
      {extra &&
        <Typography sx={dontBreak} variant="body2" color="textSecondary">{extra}</Typography>
      }
    </Grid>
  );
};

export default Display;
