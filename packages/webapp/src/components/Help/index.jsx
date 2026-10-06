import { useEffect, useState } from 'react';
import { Link, Route, Routes, useParams, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import {
  CircularProgress,
  Grid,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material';

import BookmarksIcon from '@mui/icons-material/Bookmarks';
import BuildIcon from '@mui/icons-material/Build';
import LibraryMusicIcon from '@mui/icons-material/LibraryMusic';
import PlayCircleIcon from '@mui/icons-material/PlayCircle';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import SettingsIcon from '@mui/icons-material/Settings';
import TerminalIcon from '@mui/icons-material/Terminal';

import Header from '../Header';
import Markdown from './markdown';

const TOPICS = [
  ['start', RocketLaunchIcon],
  ['player', PlayCircleIcon],
  ['library', LibraryMusicIcon],
  ['cards', BookmarksIcon],
  ['settings', SettingsIcon],
  ['lauschctl', TerminalIcon],
  ['troubleshooting', BuildIcon],
];

const LANGUAGES = ['de', 'en'];

const HelpOverview = () => {
  const { t } = useTranslation();
  return (
    <>
      <Header title={t('navigation.help')} />
      <List sx={{ width: '100%' }}>
        {TOPICS.map(([id, Icon]) => (
          <ListItem disablePadding key={id}>
            <ListItemButton component={Link} nativeButton={false} to={`/help/${id}`}>
              <ListItemIcon><Icon /></ListItemIcon>
              <ListItemText primary={t(`help.topics.${id}.title`)} secondary={t(`help.topics.${id}.subtitle`)} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </>
  );
};

const HelpTopic = () => {
  const { t, i18n } = useTranslation();
  const { topic } = useParams();
  const [searchParams] = useSearchParams();
  const section = searchParams.get('section');
  const [source, setSource] = useState(null);
  const [failed, setFailed] = useState(false);
  const known = TOPICS.some(([id]) => id === topic);
  const language = LANGUAGES.find((code) => (i18n.language || '').startsWith(code)) || 'en';

  useEffect(() => {
    if (!known) return;
    let active = true;
    setSource(null);
    setFailed(false);
    fetch(`/help/${language}/${topic}.md`)
      .then((response) => (response.ok ? response.text() : Promise.reject(new Error(response.statusText))))
      .then((text) => {
        if (active) setSource(text);
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => {
      active = false;
    };
  }, [known, language, topic]);

  useEffect(() => {
    if (source && section) document.getElementById(section)?.scrollIntoView();
  }, [source, section]);

  return (
    <>
      <Header backLink="/help" title={known && source ? '' : t('navigation.help')} />
      <Stack sx={{ padding: '0 16px 16px', width: '100%' }}>
        {!known || failed ? <Typography>{t('help.not-found')}</Typography> : null}
        {known && !failed && !source && <CircularProgress />}
        {source && <Markdown source={source} />}
      </Stack>
    </>
  );
};

const Help = () => (
  <Grid container id="help" size={12}>
    <Routes>
      <Route index element={<HelpOverview />} />
      <Route path=":topic" element={<HelpTopic />} />
    </Routes>
  </Grid>
);

export { TOPICS };
export default Help;
