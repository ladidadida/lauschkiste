import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, test, vi } from 'vitest';

import request from '../../../utils/request';
import SambaSettings from './samba';

vi.mock('../../../utils/request', () => ({ default: vi.fn(), requestErrorMessage: () => null }));
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key, options = {}) => [key, options.user, options.address].filter(Boolean).join(' ') }),
}));

test('shows how to log in to the share', async () => {
  request.mockResolvedValue({ result: {
    installed: true, shared: true, outdated: false, has_password: true, user: 'loma',
    path: '/home/pi/lauschkiste/library', address: 'smb://lauschkiste-box/lauschkiste',
  } });
  render(<MemoryRouter><SambaSettings /></MemoryRouter>);
  expect(await screen.findByText('settings.samba.login-user loma')).toBeInTheDocument();
  expect(screen.getByText('settings.samba.login-windows \\\\lauschkiste-box\\lauschkiste')).toBeInTheDocument();
  expect(screen.getByText('settings.samba.login-mac smb://lauschkiste-box/lauschkiste')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'settings.cli.more' })).toHaveAttribute('href', '/help/library?section=samba');
});
