import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import PubSubContext from '../../context/pubsub/context';
import { refreshLibrary } from '../../utils/library-api';
import LibraryHeader, { activeTabAndView } from './library-header';

vi.mock('../../utils/library-api', () => ({ refreshLibrary: vi.fn() }));
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (key) => key }) }));

const renderHeader = (state = {}) => render(
  <PubSubContext.Provider value={{ state }}>
    <MemoryRouter initialEntries={['/library/overview']}>
      <LibraryHeader handleMusicFilter={() => {}} musicFilter="" />
    </MemoryRouter>
  </PubSubContext.Provider>,
);

describe('LibraryHeader refresh', () => {
  beforeEach(() => {
    refreshLibrary.mockReset();
  });

  test('starts a rescan and waits for the scan event', async () => {
    refreshLibrary.mockResolvedValue({ scanning: true });
    const { rerender } = renderHeader();

    const button = screen.getByRole('button', { name: 'library.header.refresh' });
    await userEvent.click(button);

    expect(refreshLibrary).toHaveBeenCalledTimes(1);
    expect(button).toBeDisabled();

    await act(async () => {
      rerender(
        <PubSubContext.Provider value={{ state: { 'library.scanned': { songs: 48 } } }}>
          <MemoryRouter initialEntries={['/library/overview']}>
            <LibraryHeader handleMusicFilter={() => {}} musicFilter="" />
          </MemoryRouter>
        </PubSubContext.Provider>,
      );
    });
    expect(screen.getByRole('button', { name: 'library.header.refresh' })).toBeEnabled();
  });

  test('re-enables the button when the request fails', async () => {
    refreshLibrary.mockRejectedValue(new Error('offline'));
    renderHeader();

    const button = screen.getByRole('button', { name: 'library.header.refresh' });
    await userEvent.click(button);

    expect(button).toBeEnabled();
  });
});

describe('LibraryHeader tabs', () => {
  test('shows the content types, only music while selecting for a card', () => {
    const { unmount } = renderHeader();
    for (const tab of ['continue', 'music', 'audiobooks', 'radio', 'podcasts']) {
      expect(screen.getByRole('tab', { name: `library.header.${tab}` })).toBeInTheDocument();
    }
    unmount();

    render(
      <PubSubContext.Provider value={{ state: {} }}>
        <MemoryRouter initialEntries={['/library/music/albums']}>
          <LibraryHeader handleMusicFilter={() => {}} isSelecting musicFilter="" />
        </MemoryRouter>
      </PubSubContext.Provider>,
    );
    expect(screen.getByRole('tab', { name: 'library.header.music' })).toBeInTheDocument();
    expect(screen.queryByRole('tab', { name: 'library.header.radio' })).not.toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'library.header.folders' })).toBeInTheDocument();
  });
});

describe('activeTabAndView', () => {
  test.each([
    ['/library/music/albums', ['music', 'albums']],
    ['/library/music/folders/music%2FRock', ['music', 'folders']],
    ['/library/mpd/albums/Artist/Album', ['music', 'albums']],
    ['/library/audiobooks', ['audiobooks', 'books']],
    ['/library/audiobooks/folders/audiobooks', ['audiobooks', 'folders']],
    ['/library/podcasts/kakadu', ['podcasts', undefined]],
    ['/library/local/folders/x', [false, undefined]],
  ])('%s', (path, expected) => {
    expect(activeTabAndView(path)).toEqual(expected);
  });
});
