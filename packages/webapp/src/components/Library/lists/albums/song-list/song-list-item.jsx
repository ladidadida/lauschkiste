import { memo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  ListItem,
  ListItemButton,
  ListItemText,
} from '@mui/material';

import { toHHMMSS } from '../../../../../utils/utils';
import request from '../../../../../utils/request'
import { LOCAL_LIBRARY_SOURCE } from '../../../../../config';
import AddToPlaylist from '../../../content/add-to-playlist';
import ItemMenu from '../../../content/item-menu';

const SongListItem = ({
  isSelecting,
  registerMusicToCard,
  song,
}) => {
  const { t } = useTranslation();
  const [isAdding, setIsAdding] = useState(false);

  const command = 'play_single';
  const {
    artist,
    duration,
    file,
    provider,
    title,
  } = song;

  const playSingle = () => {
    request(command, { song_url: file, provider })
  }

  const registerSongToCard = () => (
    registerMusicToCard(command, { song_url: file, provider })
  );

  const canAdd = !isSelecting && (!provider || provider === LOCAL_LIBRARY_SOURCE);

  return (
    <ListItem
      disablePadding
      secondaryAction={canAdd &&
        <ItemMenu
          items={[{ label: t('library.playlists.add-song-to'), onClick: () => setIsAdding(true) }]}
          label={t('library.content.more')}
        />
      }
    >
      <ListItemButton
        role={undefined}
        onClick={() => (isSelecting ? registerSongToCard() : playSingle())}
      >
        <ListItemText
          primary={title || t('library.albums.unknown-title')}
          secondary={`${artist || t('library.albums.unknown-artist')} • ${toHHMMSS(duration)}`}
        />
      </ListItemButton>
      {canAdd && <AddToPlaylist files={[file]} onClose={() => setIsAdding(false)} open={isAdding} />}
    </ListItem>
  );
}

export default memo(SongListItem);
