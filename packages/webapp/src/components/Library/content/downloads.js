import { useCallback, useEffect, useState } from 'react';

import request from '../../../utils/request';

const ACTIVE = ['downloading', 'queued'];

// The downloads of the cache by `source/item`; reloads while one is running.
export const useDownloads = (enabled = true) => {
  const [downloads, setDownloads] = useState({});

  const reload = useCallback(async () => {
    const { result } = await request('cacheDownloads');
    setDownloads(result ? Object.fromEntries(result.items.map((entry) => [`${entry.source}/${entry.item}`, entry])) : {});
  }, []);

  useEffect(() => {
    if (enabled) reload();
  }, [enabled, reload]);

  const running = Object.values(downloads).some(({ state }) => ACTIVE.includes(state));
  useEffect(() => {
    if (!running) return undefined;
    const timer = setInterval(reload, 3000);
    return () => clearInterval(timer);
  }, [running, reload]);

  return [downloads, reload];
};

// What to show about a download (a line of text, empty when there is nothing to say).
export const downloadStatus = (t, download) => {
  if (!download) return '';
  const percent = download.total ? Math.floor((100 * download.done) / download.total) : 0;
  return {
    queued: t('library.downloads.queued'),
    downloading: t('library.downloads.downloading', { progress: percent }),
    error: t('library.downloads.download-error'),
    done: download.update_available ? t('library.downloads.update-available') : '',
  }[download.state] || '';
};

// The menu entries to download, stop or remove an item of a source.
export const downloadMenuItems = (t, { source, item, download, onChanged }) => {
  const run = async (command) => {
    await request(command, { source, item });
    onChanged();
  };
  const state = download?.state;
  if (state === 'done') {
    return [
      ...(download.update_available
        ? [{
          label: t('library.downloads.download-again'),
          onClick: async () => {
            await request('cacheRemove', { source, item });
            await run('cacheDownload');
          },
        }]
        : []),
      { label: t('library.downloads.remove-download'), onClick: () => run('cacheRemove') },
    ];
  }
  if (ACTIVE.includes(state)) {
    return [{ label: t('library.downloads.cancel-download'), onClick: () => run('cacheCancel') }];
  }
  return [{ label: t('library.downloads.download'), onClick: () => run('cacheDownload') }];
};
