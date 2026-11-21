import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import request from '../../../utils/request';
import AddToPlaylist from './add-to-playlist';
import PlaylistEditor from './playlist-editor';
import Playlists from './playlists';

vi.mock('../../../utils/request', () => ({ default: vi.fn(), requestErrorMessage: () => null }));
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (key) => key }) }));

const SUMMARY = { id: 'mix', title: 'Mix', tracks: 2, duration: 120, cover_url: null };
const PLAYLIST = {
  id: 'mix',
  title: 'Mix',
  entries: [
    { file: 'music/a.mp3', title: 'A', artist: 'X', duration: 60, missing: false },
    { file: 'music/b.mp3', title: 'B', artist: 'Y', duration: 60, missing: false },
  ],
};

beforeEach(() => {
  request.mockReset();
  request.mockImplementation(async (command, args) => {
    if (command === 'playlistsList') return { result: [SUMMARY] };
    if (command === 'playlistGet') return { result: PLAYLIST };
    if (command === 'playlistSave') {
      return { result: { ...PLAYLIST, title: args.title, entries: args.files.map((file) => ({ file, title: file })) } };
    }
    if (command === 'librarySearch') return { result: [{ file: 'music/c.mp3', title: 'C', duration: 30 }] };
    if (command === 'playlistCreate') return { result: { id: 'neu', title: args.title, entries: [] } };
    return { result: null };
  });
});

const renderAt = (path) => render(
  <MemoryRouter initialEntries={[path]}>
    <Routes>
      <Route path="/library/music/playlists" element={<Playlists musicFilter="" />} />
      <Route path="/library/music/playlists/:playlist" element={<PlaylistEditor />} />
    </Routes>
  </MemoryRouter>,
);

test('lists playlists and plays one', async () => {
  renderAt('/library/music/playlists');
  await userEvent.click(await screen.findByText('Mix'));
  expect(request).toHaveBeenCalledWith('playlist_play', { playlist: 'mix' });
});

test('creates a playlist and opens it', async () => {
  renderAt('/library/music/playlists');
  await userEvent.click(await screen.findByRole('button', { name: 'library.playlists.new' }));
  await userEvent.type(screen.getByLabelText(/library.playlists.title-label/), 'Neu');
  await userEvent.click(screen.getByRole('button', { name: 'library.playlists.create' }));
  await waitFor(() => expect(request).toHaveBeenCalledWith('playlistGet', { playlist: 'neu' }));
});

test('reorders, removes and adds songs, then saves', async () => {
  renderAt('/library/music/playlists/mix');
  await userEvent.click((await screen.findAllByRole('button', { name: 'library.playlists.move-down' }))[0]);
  await userEvent.click(screen.getAllByRole('button', { name: 'library.playlists.remove' })[1]);
  await userEvent.type(screen.getByLabelText('library.playlists.search-label'), 'cc');
  await userEvent.click(await screen.findByRole('button', { name: 'library.playlists.add-song' }));
  await userEvent.click(screen.getByRole('button', { name: 'general.buttons.save' }));
  await waitFor(() => expect(request).toHaveBeenCalledWith('playlistSave', {
    playlist: 'mix', title: 'Mix', files: ['music/b.mp3', 'music/c.mp3'],
  }));
  expect(await screen.findByRole('button', { name: 'library.playlists.saved' })).toBeDisabled();
});

test('adds songs to an existing or a new playlist', async () => {
  render(<AddToPlaylist files={['music/a.mp3']} onClose={vi.fn()} open />);
  await userEvent.click(await screen.findByText('Mix'));
  expect(request).toHaveBeenCalledWith('playlistAdd', { playlist: 'mix', files: ['music/a.mp3'] });
  await userEvent.type(screen.getByLabelText('library.playlists.new-title'), 'Neu');
  await userEvent.click(screen.getByRole('button', { name: 'library.playlists.create' }));
  expect(request).toHaveBeenCalledWith('playlistCreate', { title: 'Neu', files: ['music/a.mp3'] });
});
