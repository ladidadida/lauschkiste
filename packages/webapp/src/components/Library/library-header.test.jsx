import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import PubSubContext from '../../context/pubsub/context';
import { refreshLibrary } from '../../utils/library-api';
import LibraryHeader from './library-header';

vi.mock('../../utils/library-api', () => ({ refreshLibrary: vi.fn() }));
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (key) => key }) }));

const renderHeader = (state = {}) => render(
  <PubSubContext.Provider value={{ state }}>
    <MemoryRouter initialEntries={['/library/overview']}>
      <LibraryHeader handleMusicFilter={() => {}} musicFilter="" sources={[]} />
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
            <LibraryHeader handleMusicFilter={() => {}} musicFilter="" sources={[]} />
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
