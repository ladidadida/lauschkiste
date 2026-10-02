import { LOCAL_LIBRARY_SOURCE } from '../../config';

const folderLink = (folder) => {
  const path = (folder || '').replace(/^\.?\/+|\/+$/g, '');
  const root = path.split('/')[0] === 'audiobooks' ? 'audiobooks' : 'music';
  return `/library/${root}/folders/${encodeURIComponent(path || root)}`;
};

// Where the library shows what is playing, from the player status' context.
const libraryLink = (context) => {
  const { action, args = {} } = context || {};
  switch (action) {
    case 'player.play_album':
      return `/library/${args.provider || LOCAL_LIBRARY_SOURCE}/albums/${
        encodeURIComponent(args.albumartist || '')}/${encodeURIComponent(args.album || '')}`;
    case 'player.play_folder':
      return folderLink(args.folder);
    case 'player.play_single':
      return folderLink((args.song_url || '').split('/').slice(0, -1).join('/'));
    case 'audiobooks.play':
      return '/library/audiobooks';
    case 'podcasts.play':
      return `/library/podcasts/${encodeURIComponent(args.podcast || '')}`;
    case 'radio.play':
      return '/library/radio';
    default:
      return '/library';
  }
};

const contentKind = (context) => context?.kind || 'music';

export { contentKind, libraryLink };
