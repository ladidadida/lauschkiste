import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, test } from 'vitest';

import Markdown, { parse, slug } from './markdown';

const SOURCE = `# Title

Some **bold** and \`code\`, see [settings](/settings) or [site](https://example.org).

## Steps

## Lesegerät {#reader}
1. First
2. Second
   continued

- A
- B

\`\`\`
lauschctl setup samba
\`\`\`

| Command | Use |
| --- | --- |
| \`home\` | shows the home |

<script>alert(1)</script>
`;

test('parses the supported blocks', () => {
  expect(parse(SOURCE).map(({ type }) => type)).toEqual(
    ['heading', 'paragraph', 'heading', 'heading', 'list', 'list', 'code', 'table', 'paragraph']);
  expect(parse(SOURCE)[4].items).toEqual(['First', 'Second continued']);
  expect(slug('Karten anlernen & löschen')).toBe('karten-anlernen-löschen');
});

test('renders links and never raw HTML', () => {
  const { container } = render(<MemoryRouter><Markdown source={SOURCE} /></MemoryRouter>);
  expect(screen.getByRole('link', { name: 'settings' })).toHaveAttribute('href', '/settings');
  expect(screen.getByRole('link', { name: 'site' })).toHaveAttribute('target', '_blank');
  expect(screen.getByRole('heading', { name: 'Steps' })).toHaveAttribute('id', 'steps');
  expect(screen.getByRole('heading', { name: 'Lesegerät' })).toHaveAttribute('id', 'reader');
  expect(container.querySelector('script')).toBeNull();
  expect(screen.getByText('<script>alert(1)</script>')).toBeInTheDocument();
});
