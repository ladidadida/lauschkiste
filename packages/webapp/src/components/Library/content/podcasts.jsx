import { useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import {
  Alert,
  Avatar,
  Badge,
  Box,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemAvatar,
  ListItemButton,
  ListItemText,
  Typography,
} from '@mui/material';

import AddIcon from '@mui/icons-material/Add';
import PodcastsIcon from '@mui/icons-material/Podcasts';

import PubSubContext from '../../../context/pubsub/context';
import request, { requestErrorMessage } from '../../../utils/request';
import { PODCASTS_TOPIC } from '../../../config';
import FormDialog from './form-dialog';
import ItemMenu from './item-menu';
import DirectorySearch from './directory-search';
import { podcastKind } from './directory-kinds';

const Podcasts = ({ musicFilter }) => {
  const { t } = useTranslation();
  const [podcasts, setPodcasts] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [directories, setDirectories] = useState([]);
  const [notice, setNotice] = useState(null);
  const fileInput = useRef(null);
  const { state: { [PODCASTS_TOPIC]: changed } = {} } = useContext(PubSubContext);

  const load = useCallback(async () => {
    const { result, error: requestError } = await request('podcastsList');
    setIsLoading(false);
    setError(requestError || null);
    if (result) setPodcasts(result);
  }, []);

  useEffect(() => {
    if (changed?.podcasts) {
      setPodcasts(changed.podcasts);
      setIsLoading(false);
    }
    else {
      load();
    }
  }, [changed, load]);

  useEffect(() => {
    request('podcastDirectories').then(({ result }) => setDirectories(result || []));
  }, []);

  const importFile = async (event) => {
    const [file] = event.target.files;
    event.target.value = '';
    if (!file) return;
    const { result, error: requestError } = await request('importPodcastOpml', { content: await file.text() });
    if (requestError) setNotice({ severity: 'error', text: requestErrorMessage(requestError) || t('library.podcasts.opml-failed') });
    else if (result.added.length) setNotice({ severity: 'success', text: t('library.podcasts.opml-imported', { count: result.added.length }) });
    else setNotice({ severity: 'info', text: t('library.podcasts.opml-nothing') });
    load();
  };

  const exportFile = async () => {
    const { result } = await request('exportPodcastOpml');
    if (!result) return;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([result.content], { type: 'text/x-opml' }));
    link.download = 'lauschkiste-podcasts.opml';
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const visible = useMemo(() => {
    const query = musicFilter.toLowerCase();
    return query ? podcasts.filter(({ name }) => name.toLowerCase().includes(query)) : podcasts;
  }, [podcasts, musicFilter]);

  if (isLoading) return <CircularProgress />;
  if (error) return <Typography>{t('library.loading-error')}</Typography>;

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ alignItems: 'center', display: 'flex', justifyContent: 'flex-end', paddingX: 1 }}>
        <Button onClick={() => (directories.length ? setIsSearching(true) : setIsAdding(true))} startIcon={<AddIcon />}>
          {t('library.podcasts.add')}
        </Button>
        <ItemMenu
          items={[
            { label: t('library.podcasts.by-address'), onClick: () => setIsAdding(true) },
            { label: t('library.podcasts.import-opml'), onClick: () => fileInput.current?.click() },
            { label: t('library.podcasts.export-opml'), onClick: exportFile },
          ]}
          label={t('library.content.more')}
        />
        <input accept=".opml,.xml,text/xml,text/x-opml" hidden onChange={importFile} ref={fileInput} type="file" />
      </Box>
      {notice && <Alert onClose={() => setNotice(null)} severity={notice.severity} sx={{ margin: 1 }}>{notice.text}</Alert>}
      {!directories.length && !podcasts.length &&
        <Typography color="text.secondary" sx={{ padding: 1 }} variant="body2">
          {t('library.podcasts.directories-missing')}
        </Typography>
      }
      {!podcasts.length && <Typography sx={{ padding: 1 }}>{t('library.podcasts.empty')}</Typography>}
      {podcasts.length > 0 && !visible.length && <Typography>{t('library.albums.no-music')}</Typography>}
      <List sx={{ width: '100%' }}>
        {visible.map((podcast) => (
          <ListItem disablePadding key={podcast.id}>
            <ListItemButton
              component={Link}
              nativeButton={false}
              to={`/library/podcasts/${encodeURIComponent(podcast.id)}`}
            >
              <ListItemAvatar>
                <Badge
                  anchorOrigin={{ horizontal: 'left', vertical: 'top' }}
                  badgeContent={podcast.unheard}
                  color="primary"
                  max={99}
                >
                  <Avatar alt="" src={podcast.image || undefined} variant="rounded">
                    <PodcastsIcon />
                  </Avatar>
                </Badge>
              </ListItemAvatar>
              <ListItemText
                primary={podcast.name}
                secondary={t('library.podcasts.episodes', {
                  count: podcast.episodes,
                  unheard: podcast.unheard,
                })}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <DirectorySearch
        directories={directories}
        kind={podcastKind}
        onAddByAddress={() => {
          setIsSearching(false);
          setIsAdding(true);
        }}
        onChanged={load}
        onClose={() => setIsSearching(false)}
        open={isSearching}
      />
      <FormDialog
        confirmLabel={t('library.podcasts.subscribe')}
        fields={[
          { name: 'url', label: t('library.podcasts.url'), required: true, type: 'url',
            helperText: t('library.podcasts.url-help') },
          { name: 'name', label: t('library.podcasts.name'), helperText: t('library.podcasts.name-help') },
        ]}
        onClose={() => setIsAdding(false)}
        onSaved={() => {
          setIsAdding(false);
          load();
        }}
        onSubmit={({ url, name }) => request('addPodcast', { url, name: name || undefined })}
        open={isAdding}
        title={t('library.podcasts.add')}
      />
    </Box>
  );
};

export default Podcasts;
