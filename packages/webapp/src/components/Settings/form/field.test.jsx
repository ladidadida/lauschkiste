import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import Field from './field';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key, options = {}) => (options.value ? `${key}:${options.value}` : options.defaultValue ?? key) }),
}));

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok: true, json: async () => [{ value: 'alsa.speakers', label: 'Built-in speakers' }],
  })));
});

afterEach(() => vi.unstubAllGlobals());

test('options come from the backend; an unknown current value stays selectable', async () => {
  const onChange = vi.fn();
  const schema = { anyOf: [{ type: 'string' }, { type: 'null' }], options: '/api/v1/volume/sinks', title: 'Device' };
  render(<Field onChange={onChange} path={['sink']} root={{}} schema={schema} value="usb.headset" />);
  await userEvent.click(screen.getByRole('combobox', { name: 'Device' }));
  expect(await screen.findByText('Built-in speakers')).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'settings.form.not-connected:usb.headset' })).toBeInTheDocument();
  await userEvent.click(screen.getByText('Built-in speakers'));
  expect(onChange).toHaveBeenCalledWith('alsa.speakers');
  expect(fetch).toHaveBeenCalledWith('/api/v1/volume/sinks');
});

test('fixed entries can be edited but not added or removed', () => {
  const schema = {
    type: 'object', fixed_keys: true, title: 'Readers',
    additionalProperties: { type: 'object', properties: {
      module: { type: 'string', readonly: true, title: 'Driver' },
      same_id_delay: { type: 'number', title: 'Delay' },
    } },
  };
  render(<Field onChange={vi.fn()} path={['readers']} root={{}} schema={schema}
    value={{ read_00: { module: 'rc522_spi', same_id_delay: 1 } }} />);
  expect(screen.getByText('read_00')).toBeInTheDocument();
  expect(screen.queryByLabelText('settings.form.new-entry')).not.toBeInTheDocument();
  expect(screen.queryByText('general.buttons.delete')).not.toBeInTheDocument();
});
