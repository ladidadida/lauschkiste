import { useContext, useEffect, useMemo, useState } from "react";
import { useTranslation } from 'react-i18next';

import {
  Chip,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";

import PubSubContext from '../../../../context/pubsub/context';
import request from '../../../../utils/request';
import { LIBRARY_SCANNED_TOPIC, LOCAL_LIBRARY_SOURCE } from '../../../../config';
import { flatByAlbum } from '../../../../utils/utils';

import AlbumList from "./album-list";

// Albums of all sources; filter chips per source once there is more than one.
const Albums = ({ musicFilter, sources = [] }) => {
  const { t } = useTranslation();
  const { state: { [LIBRARY_SCANNED_TOPIC]: lastScan } = {} } = useContext(PubSubContext);

  const [albums, setAlbums] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [source, setSource] = useState(null);

  useEffect(() => {
    let isCurrent = true;
    const fetchAlbumList = async () => {
      // A rescan reloads the list in place, without the spinner
      if (lastScan === undefined) setIsLoading(true);
      setError(null);
      const { result, error: requestError } = await request('libraryItems', { content_types: ['album'] });
      if (!isCurrent) return;
      setIsLoading(false);
      if (result) setAlbums(result.reduce(flatByAlbum, []));
      if (requestError) setError(requestError);
    };

    fetchAlbumList();
    return () => {
      isCurrent = false;
    };
  }, [lastScan]);

  const providers = useMemo(() => [...new Set(albums.map(({ provider }) => provider))], [albums]);

  const visible = useMemo(() => {
    const query = musicFilter.toLowerCase();
    return albums.filter(({ albumartist, album, provider }) => (
      (!source || provider === source) && (
        !query ||
        (albumartist || '').toLowerCase().includes(query) ||
        (album || '').toLowerCase().includes(query)
      )
    ));
  }, [albums, musicFilter, source]);

  const sourceLabel = (id) => t(`library.sources.${id}`, {
    defaultValue: sources.find((entry) => entry.id === id)?.label || id,
  });

  if (isLoading) return <CircularProgress />;
  if (error) return <Typography>{t('library.loading-error')}</Typography>;
  if (!albums.length) return <Typography sx={{ padding: 1 }}>{t('library.music.empty')}</Typography>;

  return (
    <Stack sx={{ width: '100%' }}>
      {providers.length > 1 &&
        <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 1, paddingX: 1 }}>
          <Chip
            color={source ? 'default' : 'primary'}
            label={t('library.music.all-sources')}
            onClick={() => setSource(null)}
          />
          {[LOCAL_LIBRARY_SOURCE, ...providers.filter((id) => id !== LOCAL_LIBRARY_SOURCE)]
            .filter((id) => providers.includes(id))
            .map((id) => (
              <Chip
                color={source === id ? 'primary' : 'default'}
                key={id}
                label={sourceLabel(id)}
                onClick={() => setSource(id)}
              />
            ))}
        </Stack>
      }
      {visible.length
        ? <AlbumList albums={visible} musicFilter={musicFilter} view="albums" />
        : <Typography sx={{ padding: 1 }}>{t('library.albums.no-music')}</Typography>
      }
    </Stack>
  );
};

export default Albums;
