import { expect, test } from 'vitest';

import { albumsOf } from './music-search';

test('albums of found songs, once each, falling back to the artist', () => {
  expect(albumsOf([
    { file: 'music/a/1.mp3', album: 'Loud', albumartist: 'Band', artist: 'X' },
    { file: 'music/a/2.mp3', album: 'Loud', albumartist: 'Band', artist: 'Y' },
    { file: 'music/b/1.mp3', album: 'Night', artist: 'Singer' },
    { file: 'music/c/1.mp3' },
  ])).toEqual([
    { album: 'Loud', albumartist: 'Band' },
    { album: 'Night', albumartist: 'Singer' },
  ]);
});
