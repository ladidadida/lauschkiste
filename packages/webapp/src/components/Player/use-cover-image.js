import { useContext, useEffect, useState } from 'react';

import AppSettingsContext from '../../context/appsettings/context';
import request from '../../utils/request';
import { coverSrc } from '../../utils/utils';

const FADE = 'linear-gradient(to bottom, rgba(18, 18, 18, 0.5), rgba(18, 18, 18, 1))';

// The cover of what plays (from the status or looked up by file) and the blurred backdrop made of it.
const useCoverImage = (playerstatus) => {
  const { cover_url, file, provider } = playerstatus || {};
  const { settings: { show_covers } = {} } = useContext(AppSettingsContext);
  const [coverImage, setCoverImage] = useState(undefined);
  const [backgroundImage, setBackgroundImage] = useState('none');

  useEffect(() => {
    const show = (cover) => {
      setCoverImage(cover);
      setBackgroundImage([FADE, `url(${cover})`].join(','));
    };
    const getCoverArt = async () => {
      // The status names the playback backend; the built-in one plays the local library
      const { result } = await request('getSingleCoverArt', {
        song_url: file,
        provider: provider === 'local_audio' ? undefined : provider,
      });
      const coverUrl = result?.cover_url;
      if (coverUrl) show(coverSrc(coverUrl));
    };

    setCoverImage(undefined);
    setBackgroundImage('none');
    if (cover_url && show_covers) show(coverSrc(cover_url));
    else if (file && show_covers) getCoverArt();
  }, [cover_url, file, provider, show_covers]);

  return { backgroundImage, coverImage };
};

export default useCoverImage;
