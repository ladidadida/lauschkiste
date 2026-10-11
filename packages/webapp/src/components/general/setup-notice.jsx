import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';

import request from '../../utils/request';

const STORAGE_KEY = 'lauschkiste.dismissed-notes';

const read = () => {
  try {
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || '[]');
    return Array.isArray(stored) ? stored : [];
  } catch {
    return [];
  }
};

const write = (keys) => {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
  } catch {
    // dismissing then lasts until the page is reloaded
  }
};

export const noteKey = ({ id, text }) => `${id}:${text}`;

// What the box says about its own set-up that the user may want to check (hardware notes of the board).
const SetupNotice = ({ dismissible = true }) => {
  const { t } = useTranslation();
  const [notes, setNotes] = useState([]);
  const [dismissed, setDismissed] = useState(read);

  useEffect(() => {
    let active = true;
    request('hardwareState').then(({ result }) => {
      if (active) setNotes(result?.notes || []);
    });
    return () => {
      active = false;
    };
  }, []);

  const shown = notes.filter((note) => note.level === 'todo' && !dismissed.includes(noteKey(note)));
  if (!shown.length) return null;

  const dismiss = (note) => {
    const keys = [...dismissed, noteKey(note)];
    setDismissed(keys);
    write(keys);
  };

  return (
    <Stack spacing={1} sx={{ margin: 1, width: '100%' }}>
      {shown.map((note) => (
        <Alert
          action={
            <>
              <Button color="inherit" component={Link} size="small" to="/settings/hardware">
                {t('setup-notice.details')}
              </Button>
              {dismissible &&
                <Button color="inherit" onClick={() => dismiss(note)} size="small">{t('setup-notice.dismiss')}</Button>
              }
            </>
          }
          key={noteKey(note)}
          severity="warning"
        >
          {note.text}
          {note.hint && <> ({t('setup-notice.hint')} <code>{note.hint}</code>)</>}
        </Alert>
      ))}
    </Stack>
  );
};

export default SetupNotice;
