import { expect, test } from 'vitest';

import { changedFields, defaultFor, fieldKind, unwrap } from './schema';

const root = {
  $defs: {
    ActionEntry: { type: 'object', widget: 'action', properties: { action: { type: 'string' }, args: { type: 'object' } } },
    Button: { type: 'object', properties: { pin: { type: 'integer', minimum: 0 }, pull_up: { type: 'boolean', default: true },
      on_press: { anyOf: [{ $ref: '#/$defs/ActionEntry' }, { type: 'null' }], default: null } } },
  },
};

test('optional fields are unwrapped', () => {
  const { schema, nullable } = unwrap({ anyOf: [{ type: 'integer', maximum: 5 }, { type: 'null' }], title: 'X' }, root);
  expect(nullable).toBe(true);
  expect(schema).toMatchObject({ type: 'integer', maximum: 5, title: 'X' });
  expect(fieldKind(unwrap({ anyOf: [{ $ref: '#/$defs/ActionEntry' }, { type: 'null' }] }, root).schema)).toBe('action');
});

test('field kinds', () => {
  expect(fieldKind({ type: 'string', enum: ['a'] })).toBe('enum');
  expect(fieldKind({ type: 'boolean' })).toBe('boolean');
  expect(fieldKind({ type: 'number' })).toBe('number');
  expect(fieldKind({ type: 'object', additionalProperties: { $ref: '#/$defs/Button' } })).toBe('dict');
  expect(fieldKind({ type: 'object', properties: {} })).toBe('object');
});

test('defaults for new entries', () => {
  expect(defaultFor({ $ref: '#/$defs/Button' }, root)).toEqual({ pin: 0, pull_up: true, on_press: null });
  expect(defaultFor({ $ref: '#/$defs/ActionEntry' }, root)).toEqual({ action: '', args: {} });
});

test('changed fields', () => {
  expect(changedFields({ a: 1, b: { c: 2 }, d: 3 }, { a: 1, b: { c: 1 }, d: 3 })).toEqual({ b: { c: 2 } });
});

test('definitions lend their type, not their title or description', () => {
  const schemaRoot = { $defs: { A: { type: 'object', title: 'A', description: 'Type docs', widget: 'action' } } };
  const { schema } = unwrap({ anyOf: [{ $ref: '#/$defs/A' }, { type: 'null' }], title: 'Field' }, schemaRoot);
  expect(schema.title).toBe('Field');
  expect(schema.description).toBeUndefined();
  expect(schema.widget).toBe('action');
});
