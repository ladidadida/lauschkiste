import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, test, vi } from 'vitest';

import PubSubContext from '../../../context/pubsub/context';
import request from '../../../utils/request';
import CardFromPlayer from './card-from-player';

vi.mock('../../../utils/request', () => ({ default: vi.fn(), requestErrorMessage: () => null }));
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (key) => key }) }));

const context = { kind: 'audiobook', title: 'Pippi', action: 'audiobooks.play', args: { book: 'Pippi' } };

const view = (detected) => (
  <PubSubContext.Provider value={{ state: detected ? { 'rfid.card_detected': detected } : {} }}>
    <CardFromPlayer context={context} />
  </PubSubContext.Provider>
);

beforeEach(() => {
  request.mockReset();
  request.mockResolvedValue({ result: null });
});

test('registers the playing item on the next unknown card', async () => {
  const { rerender } = render(view({ card_id: 'old', registered: true, learned: false }));
  await userEvent.click(screen.getByRole('button', { name: 'player.card.title' }));
  expect(request).toHaveBeenCalledWith('rfidLearn', { seconds: 60 });

  await act(async () => rerender(view({ card_id: '42', registered: false, learned: true })));
  await waitFor(() => expect(request).toHaveBeenCalledWith('registerCard', {
    card_id: '42', action: 'audiobooks.play', args: { book: 'Pippi' }, overwrite: true,
  }));
  expect(await screen.findByText('player.card.done')).toBeInTheDocument();
});

test('asks before overwriting a registered card', async () => {
  const { rerender } = render(view(null));
  await userEvent.click(screen.getByRole('button', { name: 'player.card.title' }));
  await act(async () => rerender(view({ card_id: '7', registered: true, learned: true })));
  expect(await screen.findByText('player.card.overwrite')).toBeInTheDocument();
  expect(request).not.toHaveBeenCalledWith('registerCard', expect.anything());
  await userEvent.click(screen.getByRole('button', { name: 'player.card.overwrite-confirm' }));
  expect(request).toHaveBeenCalledWith('registerCard', expect.objectContaining({ card_id: '7' }));
});

test('cancelling ends learning', async () => {
  render(view(null));
  await userEvent.click(screen.getByRole('button', { name: 'player.card.title' }));
  await userEvent.click(screen.getByRole('button', { name: 'general.buttons.cancel' }));
  expect(request).toHaveBeenCalledWith('rfidStopLearning');
});
