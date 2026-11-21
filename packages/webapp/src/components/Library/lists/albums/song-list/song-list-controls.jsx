import { useTranslation } from 'react-i18next';

import { useState } from 'react';

import {
  Button,
  Grid,
  IconButton,
} from '@mui/material';

import PlaylistAddIcon from '@mui/icons-material/PlaylistAdd';

import PlayCircleFilledRoundedIcon from '@mui/icons-material/PlayCircleFilledRounded';
import request from '../../../../../utils/request';
import { LOCAL_LIBRARY_SOURCE } from '../../../../../config';
import AddToPlaylist from '../../../content/add-to-playlist';

const SongListControls = ({
  albumartist,
  album,
  contentUri,
  disabled,
  files = [],
  registerMusicToCard,
  isSelecting,
  provider,
}) => {
  const { t } = useTranslation();
  const command = 'play_album';
  const [isAdding, setIsAdding] = useState(false);
  const canAdd = !isSelecting && (!provider || provider === LOCAL_LIBRARY_SOURCE);

  const playAlbum = () => (
    request(command, {
      albumartist,
      album,
      content_uri: contentUri,
      provider,
    })
  );

  const registerAlbumToCard = () => (
    registerMusicToCard(command, {
      albumartist,
      album,
      content_uri: contentUri,
      provider,
    })
  );

  return (
    <Grid container size={12} sx={{ padding: '0 8px' }}>
      <Grid size={12}
        sx={{
          display: 'flex',
          justifyContent: 'right',
        }}
      >
        {canAdd &&
          <IconButton
            aria-label={t('library.playlists.add-album-to')}
            disabled={disabled}
            onClick={() => setIsAdding(true)}
            size="large"
            title={t('library.playlists.add-album-to')}
          >
            <PlaylistAddIcon style={{ fontSize: 40 }} />
          </IconButton>
        }
        {
          !isSelecting
            ? <IconButton
                aria-label="Play"
                onClick={playAlbum}
                disabled={disabled}
                size="large"
              >
                <PlayCircleFilledRoundedIcon color="primary" style={{ fontSize: 64 }} />
              </IconButton>
            : <Button
                variant="outlined"
                onClick={registerAlbumToCard}
                sx={{ margin: '20px 0 4px' }}
              >
                {t('library.albums.assign-to-card')}
              </Button>
        }
      </Grid>
      {canAdd && <AddToPlaylist files={files} onClose={() => setIsAdding(false)} open={isAdding} />}
    </Grid>
  );
};

export default SongListControls;
