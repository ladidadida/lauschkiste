import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, test, vi } from 'vitest';

import PubSubContext from '../../../context/pubsub/context';
import request from '../../../utils/request';
import Radio from './radio';

vi.mock('../../../utils/request', () => ({ default: vi.fn(), requestErrorMessage: () => null }));
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (key) => key }) }));

const STATIONS = [{ id: 'dlf', name: 'Deutschlandfunk', url: 'https://example.org/dlf.mp3', logo: null }];

const renderRadio = () => render(
  <PubSubContext.Provider value={{ state: {} }}>
    <Radio musicFilter="" />
  </PubSubContext.Provider>,
);

beforeEach(() => {
  request.mockReset();
  request.mockImplementation(async (command) => (
    command === 'radioStations' ? { result: STATIONS } : { result: null }
  ));
});

test('lists stations and plays one', async () => {
  renderRadio();
  await userEvent.click(await screen.findByText('Deutschlandfunk'));
  expect(request).toHaveBeenCalledWith('radio_play', { station: 'dlf' });
});

test('adds a station', async () => {
  renderRadio();
  await userEvent.click(await screen.findByRole('button', { name: 'library.radio.add' }));
  await userEvent.type(screen.getByLabelText(/library.radio.name/), 'WDR 5');
  await userEvent.type(screen.getByLabelText(/library.radio.url/), 'https://example.org/wdr5');
  await userEvent.click(screen.getByRole('button', { name: 'general.buttons.save' }));
  await waitFor(() => expect(request).toHaveBeenCalledWith(
    'addRadioStation', { name: 'WDR 5', url: 'https://example.org/wdr5', logo: undefined },
  ));
});

test('shows a hint without stations', async () => {
  request.mockResolvedValue({ result: [] });
  renderRadio();
  expect(await screen.findByText('library.radio.empty')).toBeInTheDocument();
});
