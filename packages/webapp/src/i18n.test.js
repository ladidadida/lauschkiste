import { expect, test } from 'vitest';
import i18n from './i18n';

test('translation files are requested with the build id', () => {
  const { v } = i18n.options.backend.queryStringParams;
  expect(v).toMatch(/^[a-z0-9]+$/);
});
