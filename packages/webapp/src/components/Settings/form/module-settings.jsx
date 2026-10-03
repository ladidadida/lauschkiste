import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  Alert,
  Button,
  Card,
  CardActions,
  CardContent,
  CardHeader,
  CircularProgress,
  Divider,
  Stack,
} from '@mui/material';

import request, { requestErrorMessage } from '../../../utils/request';
import { useRestart } from '../restart';
import Field, { FormErrorsContext } from './field';
import { changedFields } from './schema';

// The settings of one module as a card with a form; `fields` limits it to some of them.
const ModuleSettings = ({ exclude = [], fields, module, title }) => {
  const { t } = useTranslation();
  const { refresh } = useRestart();
  const [entry, setEntry] = useState(null);
  const [values, setValues] = useState({});
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [invalid, setInvalid] = useState(new Set());
  const reportError = useCallback((id, isInvalid) => {
    setInvalid((current) => {
      if (current.has(id) === isInvalid) return current;
      const next = new Set(current);
      if (isInvalid) next.add(id);
      else next.delete(id);
      return next;
    });
  }, []);

  useEffect(() => {
    request('moduleSettings', { name: module }).then(({ result }) => {
      if (!result) {
        setUnavailable(true);
        return;
      }
      setEntry(result);
      setValues(result.values);
    });
  }, [module]);

  if (unavailable) return null;
  if (!entry) return <CircularProgress />;

  const keys = Object.keys(entry.schema.properties)
    .filter((key) => (!fields || fields.includes(key)) && !exclude.includes(key));
  const changed = changedFields(Object.fromEntries(keys.map((key) => [key, values[key]])), entry.values);
  const dirty = Object.keys(changed).length > 0;

  const save = async () => {
    setIsSaving(true);
    setError('');
    setSaved(false);
    const { result, error: requestError } = await request('updateModuleSettings', { name: module, values: changed });
    setIsSaving(false);
    if (requestError) {
      setError(requestErrorMessage(requestError) || t('settings.form.save-error'));
      return;
    }
    const next = result || { ...entry, values: { ...entry.values, ...changed } };
    setEntry(next);
    setValues(next.values);
    setSaved(true);
    refresh();
  };

  return (
    <Card>
      <CardHeader title={title || t(`settings.modules.${module}`, { defaultValue: entry.title })} />
      <Divider />
      <CardContent>
        <FormErrorsContext.Provider value={reportError}>
        <Stack spacing={2}>
          {keys.map((key) => (
            <Field
              i18nBase={`settings.fields.${module}`}
              key={key}
              onChange={(next) => {
                setSaved(false);
                setValues((current) => ({ ...current, [key]: next }));
              }}
              path={[key]}
              root={entry.schema}
              schema={entry.schema.properties[key]}
              value={values[key]}
            />
          ))}
          {error && <Alert severity="error">{error}</Alert>}
          {saved && !dirty && <Alert severity="success">{t('settings.form.saved')}</Alert>}
        </Stack>
        </FormErrorsContext.Provider>
      </CardContent>
      <CardActions sx={{ justifyContent: 'flex-end' }}>
        {dirty &&
          <Button onClick={() => setValues(entry.values)} size="small">{t('general.buttons.cancel')}</Button>
        }
        <Button disabled={!dirty || isSaving || invalid.size > 0} onClick={save} size="small" variant="contained">
          {t('general.buttons.save')}
        </Button>
      </CardActions>
    </Card>
  );
};

export default ModuleSettings;
