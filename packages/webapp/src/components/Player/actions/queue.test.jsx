import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, test, vi } from 'vitest';

import request from '../../../utils/request';
import Queue from './queue';

vi.mock('../../../utils/request', () => ({ default: vi.fn() }));
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (key) => key }) }));

beforeEach(() => {
  request.mockReset();
  request.mockImplementation(async (command) => (command === 'playerQueue' ? {
    result: [
      { position: 0, file: 'audiobooks/Pippi/01.mp3', title: 'Kapitel 1', duration: 300 },
      { position: 1, file: 'audiobooks/Pippi/02.mp3', title: null, duration: null },
    ],
  } : { result: null }));
});

test('lists the chapters and jumps to one', async () => {
  render(<Queue kind="audiobook" length={2} position={0} />);
  await userEvent.click(screen.getByRole('button', { name: 'player.queue.title.audiobook' }));
  expect(await screen.findByText('Kapitel 1')).toBeInTheDocument();
  await userEvent.click(screen.getByText('02.mp3'));
  expect(request).toHaveBeenCalledWith('jump', { position: 1 });
});

test('is disabled for a single entry', () => {
  render(<Queue kind="podcast" length={1} position={0} />);
  expect(screen.getByRole('button', { name: 'player.queue.title.podcast' })).toBeDisabled();
});
