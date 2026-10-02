import { expect, test } from 'vitest';

import commands from '../../commands';
import {
  buildActionData,
  buildCardEntry,
  findCommandByCardAction,
  getArgsValues,
} from './utils';


test('player card contracts preserve provider-qualified content', () => {
  expect(commands.play_single.argKeys).toEqual(['song_url', 'provider']);
  expect(commands.play_album.argKeys).toEqual([
    'albumartist',
    'album',
    'content_uri',
    'provider',
  ]);

  const providerAlbum = buildActionData('play_music', 'play_album', {
    albumartist: 'Artist',
    album: 'Album',
    content_uri: 'service:album:123',
    provider: 'streaming',
  });
  expect(getArgsValues(providerAlbum)).toEqual([
    'Artist',
    'Album',
    'service:album:123',
    'streaming',
  ]);

  const legacyAlbum = buildActionData(
    'play_music',
    'play_album',
    ['Artist', 'Album'],
  );
  expect(getArgsValues(legacyAlbum)).toEqual([
    'Artist',
    'Album',
    undefined,
    undefined,
  ]);
});

test('card entries use action ids and named arguments', () => {
  const album = buildActionData('play_music', 'play_album', {
    albumartist: 'Artist',
    album: 'Album',
  });
  expect(buildCardEntry(album)).toEqual({
    action: 'player.play_album',
    args: { albumartist: 'Artist', album: 'Album' },
  });

  expect(buildCardEntry(buildActionData('audio', 'next_song'))).toEqual({
    action: 'player.next',
    args: {},
  });

  expect(findCommandByCardAction('player.play_folder')).toBe('play_folder');
  expect(findCommandByCardAction('volume.set_volume')).toBeUndefined();
});

test('timer cards share the timers.start action and keep their timer name', () => {
  const card = buildActionData('timers', 'timer_fade_volume', { wait_seconds: 600 });
  expect(buildCardEntry(card)).toEqual({
    action: 'timers.start',
    args: { timer: 'fade_volume', wait_seconds: 600 },
  });
  expect(findCommandByCardAction('timers.start', { timer: 'fade_volume', wait_seconds: 600 }))
    .toBe('timer_fade_volume');
  expect(findCommandByCardAction('timers.start', { timer: 'stop_player' })).toBe('timer_stop_player');
});

test('content card actions build named args and are found again', () => {
  const book = buildActionData('audiobooks', 'audiobook_play', { book: 'Pippi' });
  expect(buildCardEntry(book)).toEqual({ action: 'audiobooks.play', args: { book: 'Pippi' } });

  const station = buildActionData('radio', 'radio_play', { station: 'dlf' });
  expect(buildCardEntry(station)).toEqual({ action: 'radio.play', args: { station: 'dlf' } });

  const newest = buildActionData('podcasts', 'podcast_play', { podcast: 'kakadu' });
  expect(buildCardEntry(newest)).toEqual({ action: 'podcasts.play', args: { podcast: 'kakadu' } });
  const episode = buildActionData('podcasts', 'podcast_play', { podcast: 'kakadu', episode: 'abc' });
  expect(buildCardEntry(episode).args).toEqual({ podcast: 'kakadu', episode: 'abc' });

  expect(findCommandByCardAction('audiobooks.restart', { book: 'x' })).toBe('audiobook_restart');
  expect(findCommandByCardAction('podcasts.play', { podcast: 'x' })).toBe('podcast_play');
});
