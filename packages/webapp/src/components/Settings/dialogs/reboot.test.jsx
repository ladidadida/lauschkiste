import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import request from '../../../utils/request';
import RebootDialog from './reboot';

vi.mock('../../../utils/request', () => ({ default: vi.fn() }));
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (key) => key }) }));

const open = async () => {
  await userEvent.click(screen.getByRole('button', { name: 'settings.dialogs.reboot.button-title' }));
  const buttons = screen.getAllByRole('button', { name: 'settings.dialogs.reboot.button-title' });
  await userEvent.click(buttons[buttons.length - 1]);
};

beforeEach(() => request.mockReset());
afterEach(() => vi.useRealTimers());

test('a failed reboot request shows the error and closes the dialog', async () => {
  request.mockResolvedValue({ error: new Error('HTTP 501') });
  render(<RebootDialog />);
  await open();
  expect(await screen.findByText('settings.dialogs.reboot.failed')).toBeInTheDocument();
  expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
});

test('keeps waiting until the backend was down and is back', async () => {
  const reload = vi.fn();
  vi.stubGlobal('location', { ...window.location, reload });
  request.mockImplementation(async (command) => (command === 'reboot' ? { result: null } : { result: {} }));
  render(<RebootDialog />);
  vi.useFakeTimers({ shouldAdvanceTime: true });
  await open();
  await vi.advanceTimersByTimeAsync(11000);
  expect(reload).not.toHaveBeenCalled();
  expect(screen.getByRole('progressbar')).toBeInTheDocument();
  request.mockImplementation(async () => ({ error: new Error('down') }));
  await vi.advanceTimersByTimeAsync(6000);
  request.mockImplementation(async () => ({ result: {} }));
  await vi.advanceTimersByTimeAsync(6000);
  expect(reload).toHaveBeenCalled();
  vi.unstubAllGlobals();
});
