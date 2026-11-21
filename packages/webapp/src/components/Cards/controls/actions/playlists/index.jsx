import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import ItemSelect from '../../item-select';
import request from '../../../../../utils/request';

const SelectPlaylists = ({
  actionData,
  handleActionDataChange,
}) => {
  const { t } = useTranslation();
  const [playlists, setPlaylists] = useState([]);
  const playlist = actionData.command?.args?.playlist;

  useEffect(() => {
    request('playlistsList').then(({ result }) => setPlaylists(result || []));
  }, []);

  return (
    <ItemSelect
      label={t('cards.controls.actions.playlists.playlist')}
      onChange={(value) => handleActionDataChange('playlists', 'playlist_play', { playlist: value })}
      options={playlists.map(({ id, title }) => ({ value: id, label: title }))}
      placeholder={playlists.length ? undefined : t('cards.controls.actions.playlists.none')}
      value={playlist}
    />
  );
};

export default SelectPlaylists;
