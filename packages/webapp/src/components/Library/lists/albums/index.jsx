import { useContext, useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';

import {
  CircularProgress,
  Typography,
} from "@mui/material";

import PubSubContext from '../../../../context/pubsub/context';
import request from '../../../../utils/request';
import { LIBRARY_SCANNED_TOPIC } from '../../../../config';
import { flatByAlbum } from '../../../../utils/utils';

import AlbumList from "./album-list";

const Albums = ({
  contentTypes,
  musicFilter,
  provider,
  view,
}) => {
  const { t } = useTranslation();
  const { state: { [LIBRARY_SCANNED_TOPIC]: lastScan } = {} } = useContext(PubSubContext);

  const [albums, setAlbums] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const search = ({ albumartist, album }) => {
    if (musicFilter === '') return true;

    const lowerCaseMusicFilter = musicFilter.toLowerCase();

    return (albumartist || '').toLowerCase().includes(lowerCaseMusicFilter) ||
      (album || '').toLowerCase().includes(lowerCaseMusicFilter);
  };

  const contentTypesKey = contentTypes?.join(',') || '';

  useEffect(() => {
    let isCurrent = true;
    const fetchAlbumList = async () => {
      // A rescan reloads the list in place, without the spinner
      if (lastScan === undefined) setIsLoading(true);
      setError(null);
      const { result, error: requestError } = await request('libraryItems', {
        provider,
        content_types: contentTypesKey ? contentTypesKey.split(',') : undefined,
      });
      if (!isCurrent) return;
      setIsLoading(false);

      if(result) setAlbums(result.reduce(flatByAlbum, []));
      if(requestError) setError(requestError);
    }

    fetchAlbumList();
    return () => {
      isCurrent = false;
    };
  }, [contentTypesKey, provider, lastScan]);

  return (
    <>
      {isLoading
        ? <CircularProgress />
        : <AlbumList
            albums={albums.filter(search)}
            musicFilter={musicFilter}
            view={view}
      />}
      {error &&
        <Typography>{t('library.loading-error')}</Typography>
      }
    </>
  );
};

export default Albums;
