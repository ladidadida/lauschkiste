import { expect, test } from 'vitest';

import { contentKind, libraryLink } from './playback-context';

test.each([
  [{ action: 'player.play_album', args: { albumartist: 'A B', album: 'C/D', provider: 'mpd' } },
    '/library/mpd/albums/A%20B/C%2FD'],
  [{ action: 'player.play_album', args: { albumartist: 'A', album: 'B' } }, '/library/local/albums/A/B'],
  [{ action: 'player.play_folder', args: { folder: 'music/Rock' } }, '/library/music/folders/music%2FRock'],
  [{ action: 'player.play_folder', args: { folder: 'audiobooks/Pippi/' } },
    '/library/audiobooks/folders/audiobooks%2FPippi'],
  [{ action: 'player.play_single', args: { song_url: 'music/Rock/01.mp3' } }, '/library/music/folders/music%2FRock'],
  [{ action: 'audiobooks.play', args: { book: 'Pippi' } }, '/library/audiobooks'],
  [{ action: 'podcasts.play', args: { podcast: 'kakadu', episode: 'x' } }, '/library/podcasts/kakadu'],
  [{ action: 'radio.play', args: { station: 'dlf' } }, '/library/radio'],
  [null, '/library'],
])('libraryLink %#', (context, expected) => {
  expect(libraryLink(context)).toBe(expected);
});

test('content kind defaults to music', () => {
  expect(contentKind(null)).toBe('music');
  expect(contentKind({ kind: 'radio' })).toBe('radio');
});
