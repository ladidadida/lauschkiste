import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import ItemSelect from '../../item-select';
import request from '../../../../../utils/request';

const SelectPodcasts = ({
  actionData,
  handleActionDataChange,
}) => {
  const { t } = useTranslation();
  const [podcasts, setPodcasts] = useState([]);
  const [episodes, setEpisodes] = useState([]);
  const { podcast, episode } = actionData.command?.args || {};

  useEffect(() => {
    request('podcastsList').then(({ result }) => setPodcasts(result || []));
  }, []);

  useEffect(() => {
    setEpisodes([]);
    if (podcast) {
      request('podcastEpisodes', { podcast }).then(({ result }) => setEpisodes(result || []));
    }
  }, [podcast]);

  const change = (args) => handleActionDataChange('podcasts', 'podcast_play', args);

  return (
    <>
      <ItemSelect
        label={t('cards.controls.actions.podcasts.podcast')}
        onChange={(value) => change({ podcast: value })}
        options={podcasts.map(({ id, name }) => ({ value: id, label: name }))}
        placeholder={podcasts.length ? undefined : t('cards.controls.actions.podcasts.none')}
        value={podcast}
      />
      {podcast &&
        <ItemSelect
          emptyLabel={t('cards.controls.actions.podcasts.newest-unheard')}
          label={t('cards.controls.actions.podcasts.episode')}
          onChange={(value) => change({ podcast, episode: value })}
          options={episodes.map(({ id, title }) => ({ value: id, label: title }))}
          value={episode}
        />
      }
    </>
  );
};

export default SelectPodcasts;
