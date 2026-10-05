import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, test, vi } from 'vitest';

import Navigation from './index';

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (key) => key }) }));

test('offers start, library, settings and help; cards count as settings', () => {
  render(<MemoryRouter initialEntries={['/cards/register']}><Navigation /></MemoryRouter>);
  const links = screen.getAllByRole('link').map((link) => link.getAttribute('href'));
  expect(links).toEqual(['/', '/library', '/settings', '/help']);
  expect(screen.getByRole('link', { name: 'navigation.settings' })).toHaveClass('Mui-selected');
});
