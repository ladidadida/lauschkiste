import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, test, vi } from 'vitest';

import request from '../../../utils/request';
import { AudiobookItem } from './audiobooks';

vi.mock('../../../utils/request', () => ({ default: vi.fn(), requestErrorMessage: () => null }));
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (key) => key }) }));

const BOOK = { book: 'Pippi', title: 'Pippi Langstrumpf', chapters: 3, source: 'local' };

beforeEach(() => {
  request.mockReset();
  request.mockResolvedValue({ result: null });
});

const openMenu = () => userEvent.click(screen.getByRole('button', { name: 'library.audiobooks.menu' }));

test('changes the title of a local audiobook', async () => {
  const onChanged = vi.fn();
  render(<AudiobookItem book={BOOK} onChanged={onChanged} />);
  await openMenu();
  await userEvent.click(screen.getByText('library.audiobooks.edit-title'));
  const field = screen.getByLabelText('library.audiobooks.title-label');
  await userEvent.clear(field);
  await userEvent.type(field, 'Pippi in Taka-Tuka-Land');
  await userEvent.click(screen.getByRole('button', { name: 'general.buttons.save' }));
  await waitFor(() => expect(onChanged).toHaveBeenCalled());
  expect(request).toHaveBeenCalledWith('audiobookSetTitle', { book: 'Pippi', title: 'Pippi in Taka-Tuka-Land' });
});

test('goes back to the title from the files', async () => {
  const onChanged = vi.fn();
  render(<AudiobookItem book={{ ...BOOK, custom_title: true }} onChanged={onChanged} />);
  await openMenu();
  await userEvent.click(screen.getByText('library.audiobooks.reset-title'));
  await waitFor(() => expect(onChanged).toHaveBeenCalled());
  expect(request).toHaveBeenCalledWith('audiobookSetTitle', { book: 'Pippi', title: '' });
});

test('books of a server cannot be renamed here', async () => {
  render(<AudiobookItem book={{ ...BOOK, source: 'audiobookshelf' }} onChanged={vi.fn()} />);
  await openMenu();
  expect(screen.queryByText('library.audiobooks.edit-title')).not.toBeInTheDocument();
});
