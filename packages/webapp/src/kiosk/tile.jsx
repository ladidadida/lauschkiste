import { useEffect, useRef, useState } from 'react';

import { Box, ButtonBase, LinearProgress, Typography } from '@mui/material';

// True once the element has come close to the visible area; lists load covers only then.
const useNearby = () => {
  const ref = useRef(null);
  const [nearby, setNearby] = useState(false);
  useEffect(() => {
    const element = ref.current;
    if (!element || nearby) return undefined;
    if (typeof IntersectionObserver === 'undefined') {
      setNearby(true);
      return undefined;
    }
    const observer = new IntersectionObserver(([entry]) => entry.isIntersecting && setNearby(true), {
      rootMargin: '300px',
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, [nearby]);
  return [ref, nearby];
};

// A big square to tap: the picture (or an icon) above a title. `loadImage` may fetch the picture lazily.
const Tile = ({ Icon, image, loadImage, onClick, progress, subtitle, title }) => {
  const [ref, nearby] = useNearby();
  const [loaded, setLoaded] = useState(null);

  useEffect(() => {
    if (!nearby || image || !loadImage) return undefined;
    let current = true;
    loadImage().then((src) => current && setLoaded(src || null));
    return () => {
      current = false;
    };
  }, [nearby, image, loadImage]);

  const src = image || loaded;
  return (
    <ButtonBase
      onClick={onClick}
      ref={ref}
      sx={{
        alignItems: 'stretch',
        bgcolor: 'background.paper',
        borderRadius: 1,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
        overflow: 'hidden',
        textAlign: 'left',
        '&:active': { opacity: 0.7 },
      }}
    >
      <Box sx={{ alignItems: 'center', aspectRatio: '1', bgcolor: 'action.hover', display: 'flex', justifyContent: 'center' }}>
        {src
          ? <img alt="" src={src} style={{ height: '100%', objectFit: 'cover', width: '100%' }} />
          : Icon && <Icon sx={{ color: 'text.secondary', fontSize: '3rem' }} />}
      </Box>
      {progress > 0 && <LinearProgress sx={{ height: 6 }} value={progress} variant="determinate" />}
      <Box sx={{ padding: 1 }}>
        <Typography sx={{ display: '-webkit-box', overflow: 'hidden', WebkitBoxOrient: 'vertical', WebkitLineClamp: 2 }}
          variant="subtitle1">
          {title}
        </Typography>
        {subtitle &&
          <Typography color="text.secondary" noWrap variant="body2">{subtitle}</Typography>}
      </Box>
    </ButtonBase>
  );
};

// The tiles of a page, as many columns as fit.
const TileGrid = ({ children }) => (
  <Box sx={{ display: 'grid', gap: 1.5, gridTemplateColumns: 'repeat(auto-fill, minmax(9rem, 1fr))', padding: 1.5 }}>
    {children}
  </Box>
);

export { Tile, TileGrid };
