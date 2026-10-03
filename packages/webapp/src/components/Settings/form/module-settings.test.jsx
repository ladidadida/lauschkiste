import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, test, vi } from 'vitest';

import request from '../../../utils/request';
import { RestartProvider } from '../restart';
import ModuleSettings from './module-settings';

vi.mock('../../../utils/request', () => ({ default: vi.fn(), requestErrorMessage: (e) => e?.message }));
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key, options = {}) => options.defaultValue ?? key }),
}));

const schema = {
  $defs: {
    ActionEntry: { type: 'object', widget: 'action', title: 'ActionEntry', required: ['action'],
      properties: { action: { type: 'string' }, args: { type: 'object', additionalProperties: true, default: {} } } },
    Button: { type: 'object', title: 'Button', required: ['pin'], properties: {
      pin: { type: 'integer', minimum: 0, maximum: 27, title: 'Pin' },
      on_press: { anyOf: [{ $ref: '#/$defs/ActionEntry' }, { type: 'null' }], default: null, title: 'When pressed' },
    } },
  },
  properties: {
    level: { type: 'integer', minimum: 0, maximum: 10, default: 3, title: 'Level' },
    mode: { type: 'string', enum: ['auto', 'pulse'], default: 'auto', title: 'Mode' },
    save: { anyOf: [{ type: 'boolean' }, { type: 'null' }], default: null, title: 'Power save' },
    buttons: { type: 'object', additionalProperties: { $ref: '#/$defs/Button' }, title: 'Buttons' },
  },
};

const entry = { name: 'demo', title: 'Demo', schema, restart_required: false,
  values: { level: 3, mode: 'auto', save: null, buttons: {} } };

beforeEach(() => {
  request.mockReset();
  request.mockImplementation(async (command, args) => {
    if (command === 'moduleSettings') return { result: entry };
    if (command === 'listActions') return { result: [{ id: 'player.next', description: 'Next song', args: { properties: {} } }] };
    if (command === 'updateModuleSettings') return { result: { ...entry, values: { ...entry.values, ...args.values } } };
    if (command === 'restartState') return { result: { required: false, modules: [] } };
    return { result: null };
  });
});

const renderForm = () => render(<RestartProvider><ModuleSettings module="demo" /></RestartProvider>);

test('renders the fields and saves only what changed', async () => {
  renderForm();
  const level = await screen.findByLabelText('Level');
  expect(screen.getByRole('combobox', { name: 'Mode' })).toBeInTheDocument();
  expect(screen.getByRole('combobox', { name: 'Power save' })).toBeInTheDocument();

  await userEvent.clear(level);
  await userEvent.type(level, '7');
  await userEvent.click(screen.getByRole('button', { name: 'general.buttons.save' }));
  await waitFor(() => expect(request).toHaveBeenCalledWith('updateModuleSettings', { name: 'demo', values: { level: 7 } }));
  expect(await screen.findByText('settings.form.saved')).toBeInTheDocument();
});

test('rejects numbers out of range', async () => {
  renderForm();
  const level = await screen.findByLabelText('Level');
  await userEvent.clear(level);
  await userEvent.type(level, '12');
  expect(screen.getByText('0 – 10')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'general.buttons.save' })).toBeDisabled();
});

test('adds a named entry with an action', async () => {
  renderForm();
  await userEvent.type(await screen.findByLabelText('settings.form.new-entry'), 'next{Enter}');
  await userEvent.click(screen.getByText('next'));
  const details = screen.getByText('next').closest('.MuiAccordion-root');
  await userEvent.click(within(details).getByRole('combobox', { name: 'When pressed' }));
  await userEvent.click(await screen.findByText('Next song'));
  await userEvent.click(screen.getByRole('button', { name: 'general.buttons.save' }));
  await waitFor(() => expect(request).toHaveBeenCalledWith('updateModuleSettings', {
    name: 'demo', values: { buttons: { next: { pin: 0, on_press: { action: 'player.next', args: {} } } } },
  }));
});
