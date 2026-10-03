// Helpers for the JSON schemas of module settings (pydantic models).

const resolve = (schema, root) => {
  if (schema?.$ref) {
    const name = schema.$ref.split('/').pop();
    // Title and description of a definition describe the type, not the field
    const { title, description, ...definition } = root?.$defs?.[name] || {}; // eslint-disable-line no-unused-vars
    return { ...definition, ...Object.fromEntries(Object.entries(schema).filter(([key]) => key !== '$ref')) };
  }
  return schema || {};
};

// A field schema without its optional wrapper (`anyOf: [X, {type: 'null'}]`), and whether it may be empty.
const unwrap = (schema, root) => {
  const resolved = resolve(schema, root);
  const variants = resolved.anyOf;
  if (Array.isArray(variants)) {
    const value = variants.find((variant) => variant.type !== 'null');
    const nullable = variants.some((variant) => variant.type === 'null');
    const { anyOf, ...rest } = resolved; // eslint-disable-line no-unused-vars
    return { schema: { ...resolve(value, root), ...rest }, nullable };
  }
  return { schema: resolved, nullable: false };
};

const fieldKind = (schema) => {
  if (schema.widget === 'action') return 'action';
  if (Array.isArray(schema.enum)) return 'enum';
  if (schema.type === 'boolean') return 'boolean';
  if (schema.type === 'integer' || schema.type === 'number') return 'number';
  if (schema.type === 'object' && schema.properties) return 'object';
  if (schema.type === 'object' && schema.additionalProperties && typeof schema.additionalProperties === 'object') {
    return 'dict';
  }
  if (schema.type === 'string') return 'string';
  return 'unsupported';
};

// Default value for a new entry of a schema (used when adding dict entries or enabling an optional object).
const defaultFor = (schema, root) => {
  const { schema: resolved } = unwrap(schema, root);
  if (resolved.default !== undefined) return resolved.default;
  switch (fieldKind(resolved)) {
    case 'object':
      return Object.fromEntries(Object.entries(resolved.properties).map(([key, value]) => {
        const { schema: field, nullable } = unwrap(value, root);
        if (field.default !== undefined || value.default !== undefined) return [key, value.default ?? field.default];
        return [key, nullable ? null : defaultFor(field, root)];
      }));
    case 'action':
      return { action: '', args: {} };
    case 'dict':
      return {};
    case 'boolean':
      return false;
    case 'number':
      return resolved.minimum ?? 0;
    case 'enum':
      return resolved.enum[0];
    default:
      return '';
  }
};

// The top-level fields that differ between two value objects.
const changedFields = (values, initial) => Object.fromEntries(
  Object.entries(values).filter(([key, value]) => JSON.stringify(value) !== JSON.stringify(initial?.[key])),
);

export { changedFields, defaultFor, fieldKind, resolve, unwrap };
