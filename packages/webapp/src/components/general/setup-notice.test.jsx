import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import request from '../../utils/request';
import SetupNotice from './setup-notice';

vi.mock('../../utils/request', () => ({ default: vi.fn() }));
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (key) => key }) }));

const notes = [
  { id: 'sound_card', level: 'todo', text: 'HiFiBerry DAC+ was found', hint: 'lauschctl setup hardware' },
  { id: 'x', level: 'ok', text: 'All fine' },
  { id: 'y', level: 'info', text: 'Just so you know' },
];

beforeEach(() => {
  window.localStorage.clear();
  request.mockReset();
  request.mockResolvedValue({ result: { notes } });
});

test('shows only what is to do, with the command', async () => {
  render(<MemoryRouter><SetupNotice /></MemoryRouter>);
  expect(await screen.findByText(/HiFiBerry DAC\+ was found/)).toBeInTheDocument();
  expect(screen.getByText('lauschctl setup hardware')).toBeInTheDocument();
  expect(screen.queryByText('All fine')).not.toBeInTheDocument();
  expect(screen.queryByText('Just so you know')).not.toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'setup-notice.details' })).toHaveAttribute('href', '/settings/hardware');
});

test('a dismissed note stays away', async () => {
  const first = render(<MemoryRouter><SetupNotice /></MemoryRouter>);
  await userEvent.click(await screen.findByRole('button', { name: 'setup-notice.dismiss' }));
  expect(screen.queryByText(/HiFiBerry DAC\+ was found/)).not.toBeInTheDocument();
  first.unmount();
  render(<MemoryRouter><SetupNotice /></MemoryRouter>);
  await vi.waitFor(() => expect(request).toHaveBeenCalledTimes(2));
  expect(screen.queryByText(/HiFiBerry DAC\+ was found/)).not.toBeInTheDocument();
});
