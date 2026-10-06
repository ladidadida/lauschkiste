import { createContext, useContext, useEffect, useId, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  FormControl,
  FormControlLabel,
  FormHelperText,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Switch,
  TextField,
  Typography,
} from '@mui/material';

import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import ActionField from './action-field';
import { defaultFor, fieldKind, unwrap } from './schema';

const NONE = '__none__';

// Fields report invalid input here, so the form can't be saved while some is.
const FormErrorsContext = createContext(() => {});

// Label and help text of a field: a translation if there is one, else the schema's title/description.
const useLabels = (i18nBase, path, schema) => {
  const { t } = useTranslation();
  const key = [i18nBase, ...path].join('.');
  const fallback = schema.title || path[path.length - 1] || '';
  return {
    label: i18nBase ? t(`${key}.label`, { defaultValue: fallback }) : fallback,
    help: i18nBase ? t(`${key}.help`, { defaultValue: schema.description || '' }) : (schema.description || ''),
  };
};

const NumberField = ({ label, help, nullable, onChange, schema, value }) => {
  const [text, setText] = useState(value ?? '');
  const [error, setError] = useState('');
  const reportError = useContext(FormErrorsContext);
  const id = useId();

  useEffect(() => {
    reportError(id, Boolean(error));
    return () => reportError(id, false);
  }, [error, id, reportError]);
  const integer = schema.type === 'integer';

  const commit = (raw) => {
    setText(raw);
    if (raw === '' && nullable) {
      setError('');
      onChange(null);
      return;
    }
    const number = Number(raw.replace(',', '.'));
    const min = schema.minimum ?? (schema.exclusiveMinimum !== undefined ? schema.exclusiveMinimum : -Infinity);
    const max = schema.maximum ?? Infinity;
    if (raw === '' || Number.isNaN(number) || (integer && !Number.isInteger(number)) || number < min || number > max) {
      setError([schema.minimum, schema.maximum].some((v) => v !== undefined)
        ? `${schema.minimum ?? '…'} – ${schema.maximum ?? '…'}` : ' ');
      return;
    }
    setError('');
    onChange(number);
  };

  return (
    <TextField
      error={Boolean(error)}
      fullWidth
      helperText={error.trim() ? error : help}
      label={label}
      onChange={(event) => commit(event.target.value)}
      size="small"
      slotProps={{ htmlInput: { inputMode: integer ? 'numeric' : 'decimal' } }}
      value={text}
    />
  );
};

// A string chosen from options the backend lists (e.g. audio devices); the current value stays
// selectable even when it is not among them right now.
const OptionsField = ({ help, label, nullable, onChange, schema, value }) => {
  const { t } = useTranslation();
  const id = useId();
  const [options, setOptions] = useState([]);

  useEffect(() => {
    let active = true;
    fetch(schema.options)
      .then((response) => (response.ok ? response.json() : []))
      .then((result) => {
        if (active) setOptions(Array.isArray(result) ? result : []);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [schema.options]);

  const known = !value || options.some((option) => option.value === value);
  return (
    <FormControl fullWidth size="small">
      <InputLabel id={`${id}-label`}>{label}</InputLabel>
      <Select
        label={label}
        labelId={`${id}-label`}
        onChange={(event) => onChange(event.target.value === NONE ? (nullable ? null : '') : event.target.value)}
        value={value || NONE}
      >
        <MenuItem value={NONE}>{nullable ? t('settings.form.default') : t('settings.form.choose')}</MenuItem>
        {!known && <MenuItem value={value}>{t('settings.form.not-connected', { value })}</MenuItem>}
        {options.map((option) => <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>)}
      </Select>
      <FormHelperText>{options.length || known ? help : t('settings.form.no-options')}</FormHelperText>
    </FormControl>
  );
};

const EnumField = ({ help, kind, label, nullable, onChange, schema, value }) => {
  const { t } = useTranslation();
  const id = useId();
  const options = kind === 'boolean' ? [true, false] : schema.enum;
  const optionLabel = (option) => (kind === 'boolean'
    ? t(option ? 'settings.form.on' : 'settings.form.off')
    : t(`settings.values.${option}`, { defaultValue: String(option) }));
  const current = value === null || value === undefined ? NONE : JSON.stringify(value);
  return (
    <FormControl fullWidth size="small">
      <InputLabel id={`${id}-label`}>{label}</InputLabel>
      <Select
        label={label}
        labelId={`${id}-label`}
        onChange={(event) => onChange(event.target.value === NONE ? null : JSON.parse(event.target.value))}
        value={current}
      >
        {nullable && <MenuItem value={NONE}>{t('settings.form.default')}</MenuItem>}
        {options.map((option) => (
          <MenuItem key={String(option)} value={JSON.stringify(option)}>{optionLabel(option)}</MenuItem>
        ))}
      </Select>
      {help && <FormHelperText>{help}</FormHelperText>}
    </FormControl>
  );
};

const DictField = ({ i18nBase, label, help, onChange, path, root, schema, value }) => {
  const fixed = Boolean(schema.fixed_keys);
  const { t } = useTranslation();
  const [name, setName] = useState('');
  const entries = Object.entries(value || {});
  const itemSchema = schema.additionalProperties;

  const add = () => {
    const key = name.trim();
    if (!key || key in (value || {})) return;
    onChange({ ...(value || {}), [key]: defaultFor(itemSchema, root) });
    setName('');
  };

  const remove = (key) => {
    const next = { ...(value || {}) };
    delete next[key];
    onChange(next);
  };

  return (
    <Box>
      <Typography variant="subtitle2">{label}</Typography>
      {help && <Typography color="text.secondary" variant="caption">{help}</Typography>}
      {entries.map(([key, entry]) => (
        <Accordion disableGutters key={key} variant="outlined">
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography sx={{ flex: 1 }}>{key}</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Field
              i18nBase={i18nBase}
              onChange={(next) => onChange({ ...(value || {}), [key]: next })}
              path={[...path, '*']}
              root={root}
              schema={itemSchema}
              value={entry}
              withoutLabel
            />
            {!fixed &&
              <Button color="error" onClick={() => remove(key)} size="small" startIcon={<DeleteIcon />} sx={{ marginTop: 1 }}>
                {t('general.buttons.delete')}
              </Button>
            }
          </AccordionDetails>
        </Accordion>
      ))}
      {fixed && !entries.length && <Typography variant="body2">{t('settings.form.no-entries')}</Typography>}
      {!fixed && <Stack direction="row" spacing={1} sx={{ alignItems: 'center', marginTop: 1 }}>
        <TextField
          label={t('settings.form.new-entry')}
          onChange={(event) => setName(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              add();
            }
          }}
          size="small"
          value={name}
        />
        <IconButton aria-label={t('settings.form.add')} disabled={!name.trim()} onClick={add}>
          <AddIcon />
        </IconButton>
      </Stack>}
    </Box>
  );
};

// One settings field, by the kind of its schema; objects and dicts recurse.
const Field = ({ i18nBase, onChange, path, root, schema: rawSchema, value, withoutLabel = false }) => {
  const { schema, nullable } = unwrap(rawSchema, root);
  const { label, help } = useLabels(i18nBase, path.filter((part) => part !== '*'), schema);
  const kind = fieldKind(schema);

  if (kind === 'boolean' && !nullable) {
    return (
      <Box>
        <FormControlLabel
          control={<Switch checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} />}
          label={label}
        />
        {help && <FormHelperText sx={{ marginTop: -1 }}>{help}</FormHelperText>}
      </Box>
    );
  }

  if (kind === 'enum' || kind === 'boolean') {
    return <EnumField help={help} kind={kind} label={label} nullable={nullable} onChange={onChange}
      schema={schema} value={value} />;
  }

  if (kind === 'options') {
    return <OptionsField help={help} label={label} nullable={nullable} onChange={onChange} schema={schema} value={value} />;
  }

  if (kind === 'number') {
    return <NumberField help={help} label={label} nullable={nullable} onChange={onChange} schema={schema} value={value} />;
  }

  if (kind === 'string') {
    return (
      <TextField
        disabled={Boolean(schema.readonly)}
        fullWidth
        helperText={help}
        label={label}
        onChange={(event) => onChange(event.target.value === '' && nullable ? null : event.target.value)}
        size="small"
        value={value ?? ''}
      />
    );
  }

  if (kind === 'action') {
    return <ActionField help={help} label={label} nullable={nullable} onChange={onChange} value={value} />;
  }

  if (kind === 'dict') {
    return (
      <DictField help={help} i18nBase={i18nBase} label={label} onChange={onChange} path={path} root={root}
        schema={schema} value={value} />
    );
  }

  if (kind === 'object') {
    const content = (
      <Stack spacing={2}>
        {Object.entries(schema.properties).map(([key, property]) => (
          <Field
            i18nBase={i18nBase}
            key={key}
            onChange={(next) => onChange({ ...(value || {}), [key]: next })}
            path={[...path, key]}
            root={root}
            schema={property}
            value={value?.[key]}
          />
        ))}
      </Stack>
    );
    if (withoutLabel) return content;
    return (
      <Box>
        <Typography sx={{ marginBottom: 1 }} variant="subtitle2">{label}</Typography>
        {help && <Typography color="text.secondary" variant="caption">{help}</Typography>}
        <Box sx={{ borderLeft: 2, borderColor: 'divider', paddingLeft: 2 }}>{content}</Box>
      </Box>
    );
  }

  return null;
};

export { FormErrorsContext };
export default Field;
