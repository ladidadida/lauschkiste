import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, test, vi } from 'vitest';

import PubSubContext from '../../../context/pubsub/context';
import request from '../../../utils/request';
import SleepTimer from './sleep-timer';

vi.mock('../../../utils/request', () => ({ default: vi.fn() }));
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (key, o = {}) => (o.count ? `${key}:${o.count}` : key) }) }));

const idle = [
  { name: 'stop_player', enabled: false, remaining_seconds: 0 },
  { name: 'fade_volume', enabled: false, remaining_seconds: 0 },
];

const renderTimer = (props = {}) => render(
  <PubSubContext.Provider value={{ state: {} }}>
    <SleepTimer kind="audiobook" stopAfterCurrent={false} {...props} />
  </PubSubContext.Provider>,
);

beforeEach(() => {
  request.mockReset();
  request.mockImplementation(async (command) => (command === 'listTimers' ? { result: idle } : { result: null }));
});

test('starts a fading timer by minutes', async () => {
  renderTimer();
  await userEvent.click(screen.getByRole('button', { name: 'player.sleep.title' }));
  await userEvent.click(screen.getByRole('button', { name: 'player.sleep.minutes:30' }));
  expect(request).toHaveBeenCalledWith('startTimer', { timer: 'fade_volume', wait_seconds: 1800 });
});

test('stops without fading when switched off', async () => {
  renderTimer();
  await userEvent.click(screen.getByRole('button', { name: 'player.sleep.title' }));
  await userEvent.click(screen.getByLabelText('player.sleep.fade'));
  await userEvent.click(screen.getByRole('button', { name: 'player.sleep.minutes:15' }));
  expect(request).toHaveBeenCalledWith('startTimer', { timer: 'stop_player', wait_seconds: 900 });
});

test('stops at the end of the chapter', async () => {
  renderTimer();
  await userEvent.click(screen.getByRole('button', { name: 'player.sleep.title' }));
  await userEvent.click(screen.getByRole('button', { name: 'player.sleep.end-of.audiobook' }));
  expect(request).toHaveBeenCalledWith('stop_after_current', { enabled: true });
});

test('shows the running timer and switches it off', async () => {
  request.mockImplementation(async (command) => (command === 'listTimers'
    ? { result: [{ name: 'stop_player', enabled: true, remaining_seconds: 600 }, idle[1]] }
    : { result: null }));
  renderTimer();
  expect(await screen.findByText('10:00')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: 'player.sleep.title' }));
  await userEvent.click(screen.getByRole('button', { name: 'player.sleep.off' }));
  await waitFor(() => expect(request).toHaveBeenCalledWith('cancelTimer', { timer: 'stop_player' }));
});
