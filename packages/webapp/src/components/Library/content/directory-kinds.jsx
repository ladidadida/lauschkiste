import PodcastsIcon from '@mui/icons-material/Podcasts';
import RadioIcon from '@mui/icons-material/Radio';

// What differs between searching for podcasts and for radio stations.
export const podcastKind = {
  Icon: PodcastsIcon,
  search: 'podcastSearch',
  top: 'podcastTop',
  texts: 'library.podcasts.search',
  add: { command: 'addPodcast', args: (hit) => ({ url: hit.feed_url, name: hit.title }), doneField: 'subscribed' },
  describe: (hit, directory) => ({
    key: `${hit.directory}/${hit.feed_url}`,
    title: hit.title,
    details: [hit.author, directory].filter(Boolean).join(' · '),
    image: hit.image,
    done: hit.subscribed,
  }),
};

export const radioKind = {
  Icon: RadioIcon,
  search: 'radioSearch',
  top: 'radioTop',
  texts: 'library.radio.search',
  add: { command: 'addRadioStation', args: (hit) => ({ name: hit.name, url: hit.url, logo: hit.logo || undefined }), doneField: 'added' },
  describe: (hit, directory) => ({
    key: `${hit.directory}/${hit.url}`,
    title: hit.name,
    details: [hit.country, hit.tags, hit.codec && hit.bitrate ? `${hit.codec} ${hit.bitrate}` : hit.codec, directory]
      .filter(Boolean).join(' · '),
    image: hit.logo,
    done: hit.added,
  }),
};
