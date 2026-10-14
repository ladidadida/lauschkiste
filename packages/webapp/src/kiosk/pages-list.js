import AutoStoriesIcon from '@mui/icons-material/AutoStories';
import HistoryIcon from '@mui/icons-material/History';
import LibraryMusicIcon from '@mui/icons-material/LibraryMusic';
import PlayCircleIcon from '@mui/icons-material/PlayCircle';
import PodcastsIcon from '@mui/icons-material/Podcasts';
import RadioIcon from '@mui/icons-material/Radio';

// The pages of the app: the player and the sections of the library, each shown when its setting is on.
const PAGES = [
  { id: 'player', Icon: PlayCircleIcon, label: 'kiosk.now-playing' },
  { id: 'continue', Icon: HistoryIcon, label: 'library.header.continue', setting: 'show_continue' },
  { id: 'music', Icon: LibraryMusicIcon, label: 'library.header.music', setting: 'show_music' },
  { id: 'audiobooks', Icon: AutoStoriesIcon, label: 'library.header.audiobooks', setting: 'show_audiobooks' },
  { id: 'radio', Icon: RadioIcon, label: 'library.header.radio', setting: 'show_radio' },
  { id: 'podcasts', Icon: PodcastsIcon, label: 'library.header.podcasts', setting: 'show_podcasts' },
];

const visiblePages = (settings) => PAGES.filter(({ setting }) => !setting || settings[setting]);

// Where the screen starts and returns to when nobody touches it.
const startPage = (settings) => {
  const pages = visiblePages(settings);
  if (settings.start_page === 'library') {
    const first = pages.find(({ id }) => id !== 'player');
    if (first) return first.id;
  }
  return 'player';
};

export { PAGES, startPage, visiblePages };
