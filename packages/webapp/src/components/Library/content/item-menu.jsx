import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';

import MoreVertIcon from '@mui/icons-material/MoreVert';

const ItemMenu = ({ items, label }) => {
  const { t } = useTranslation();
  const [anchor, setAnchor] = useState(null);

  return (
    <>
      <IconButton
        aria-label={label || t('library.content.more')}
        edge="end"
        onClick={(event) => setAnchor(event.currentTarget)}
      >
        <MoreVertIcon />
      </IconButton>
      <Menu anchorEl={anchor} onClose={() => setAnchor(null)} open={Boolean(anchor)}>
        {items.map(({ label: itemLabel, onClick }) => (
          <MenuItem
            key={itemLabel}
            onClick={() => {
              setAnchor(null);
              onClick();
            }}
          >
            {itemLabel}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
};

export default ItemMenu;
