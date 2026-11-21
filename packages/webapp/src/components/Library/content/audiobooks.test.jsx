import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, test, vi } from 'vitest';

import request from '../../../utils/request';
import { AudiobookItem } from './audiobooks';
import { moveItem } from './audiobook-editor';

vi.mock('../../../utils/request', () => ({ default: vi.fn(), requestErrorMessage: () => null }));
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (key) => key }) }));

const BOOK = { book: 'Pippi', title: 'Pippi Langstrumpf', chapters: 2, source: 'local' };
const DETAILS = {
  book: 'Pippi',
  title: 'Pippi Langstrumpf',
  tag_title: 'Pippi Langstrumpf',
  author: 'Astrid Lindgren',
  tag_author: 'Astrid Lindgren',
  cover_url: null,
  custom_cover: false,
  chapters: [
    { file: '01.mp3', title: 'Anfang', tag_title: 'Anfang', duration: 60 },
    { file: '02.mp3', title: 'Ende', tag_title: 'Ende', duration: 60 },
  ],
};

beforeEach(() => {
  request.mockReset();
  request.mockImplementation(async (command) => (
    command === 'audiobookGet' ? { result: DETAILS } : { result: null }
  ));
});

const openEditor = async () => {
  await userEvent.click(screen.getByRole('button', { name: 'library.audiobooks.menu' }));
  await userEvent.click(screen.getByText('library.audiobooks.edit'));
  return screen.findByRole('dialog');
};

test('edits title, author and chapters of a local audiobook', async () => {
  const onChanged = vi.fn();
  render(<AudiobookItem book={BOOK} onChanged={onChanged} />);
  const dialog = await openEditor();
  const title = await within(dialog).findByLabelText('library.audiobooks.title-label');
  await userEvent.clear(title);
  await userEvent.type(title, 'Pippi in Taka-Tuka-Land');
  await userEvent.clear(within(dialog).getByLabelText('library.audiobooks.author-label'));
  const chapters = within(dialog).getAllByLabelText('library.audiobooks.chapter-label');
  expect(chapters).toHaveLength(2);
  const [chapter] = chapters;
  await userEvent.clear(chapter);
  await userEvent.type(chapter, 'Los geht es');
  await userEvent.click(within(dialog).getAllByRole('button', { name: 'library.audiobooks.move-down' })[0]);
  await userEvent.click(within(dialog).getByRole('button', { name: 'general.buttons.save' }));
  await waitFor(() => expect(onChanged).toHaveBeenCalled());
  expect(request).toHaveBeenCalledWith('audiobookEdit', {
    book: 'Pippi',
    title: 'Pippi in Taka-Tuka-Land',
    author: '',
    chapters: [{ file: '02.mp3', title: 'Ende' }, { file: '01.mp3', title: 'Los geht es' }],
  });
});

test('goes back to the cover from the files', async () => {
  request.mockImplementation(async (command) => (
    command === 'audiobookGet' ? { result: { ...DETAILS, custom_cover: true } } : { result: null }
  ));
  render(<AudiobookItem book={BOOK} onChanged={vi.fn()} />);
  const dialog = await openEditor();
  await userEvent.click(await within(dialog).findByRole('button', { name: 'library.audiobooks.reset-cover' }));
  expect(request).toHaveBeenCalledWith('audiobookRemoveCover', { book: 'Pippi' });
});

test('books of a server cannot be edited here', async () => {
  render(<AudiobookItem book={{ ...BOOK, source: 'audiobookshelf' }} onChanged={vi.fn()} />);
  await userEvent.click(screen.getByRole('button', { name: 'library.audiobooks.menu' }));
  expect(screen.queryByText('library.audiobooks.edit')).not.toBeInTheDocument();
});

test('moveItem swaps neighbours and keeps the ends', () => {
  expect(moveItem(['a', 'b', 'c'], 0, 1)).toEqual(['b', 'a', 'c']);
  expect(moveItem(['a', 'b', 'c'], 0, -1)).toEqual(['a', 'b', 'c']);
  expect(moveItem(['a', 'b', 'c'], 2, 1)).toEqual(['a', 'b', 'c']);
});
