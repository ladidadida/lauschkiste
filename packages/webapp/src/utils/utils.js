const progressToTime = (duration, progress) => duration * progress / 100;
const timeToProgress = (duration, elapsed) => elapsed * 100 / duration;

const toHHMMSS = (rawSeconds) => {
  const seconds = Math.round(rawSeconds);
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return [
    h,
    m > 9 ? m : (h ? '0' + m : m || '0'),
    s > 9 ? s : '0' + (isNaN(s) ? '0' : s)
  ].filter(Boolean).join(':');
}

const flatByAlbum = (albumList, entry) => {
  const { album } = entry;
  const list = Array.isArray(album)
    ? album.map(name => ({ ...entry, album: name }))
    : [entry];

  return [...albumList, ...list];
};


// Cover URLs are absolute (http(s) or a path of this server) or names in the web app's cover cache.
const coverSrc = (coverUrl) => (
  coverUrl.startsWith('http') || coverUrl.startsWith('/') ? coverUrl : `/cover-cache/${coverUrl}`
);

export {
  coverSrc,
  flatByAlbum,
  progressToTime,
  timeToProgress,
  toHHMMSS,
}
