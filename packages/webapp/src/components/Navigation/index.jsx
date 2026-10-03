import {
  Link,
  matchPath,
  useLocation,
} from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import BottomNavigation from '@mui/material/BottomNavigation';
import BottomNavigationAction from '@mui/material/BottomNavigationAction';
import HomeIcon from '@mui/icons-material/Home';
import MusicNoteIcon from '@mui/icons-material/MusicNote';
import SettingsIcon from '@mui/icons-material/Settings';

const navigationItems = [
  {
    icon: HomeIcon,
    labelKey: 'navigation.start',
    matchPatterns: [{ path: '/', end: true }],
    to: '/',
  },
  {
    icon: MusicNoteIcon,
    labelKey: 'navigation.library',
    matchPatterns: [{ path: '/library/*' }],
    to: '/library',
  },
  {
    icon: SettingsIcon,
    labelKey: 'navigation.settings',
    matchPatterns: [{ path: '/settings/*' }, { path: '/cards/*' }],
    to: '/settings',
  },
];

export default function Navigation() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const value = navigationItems.find(({ matchPatterns }) => (
    matchPatterns.some((pattern) => matchPath(pattern, pathname))
  ))?.to ?? false;

  return (
    <BottomNavigation
      value={value}
      showLabels
      sx={{
        width: '100%',
        position: 'fixed',
        bottom: '0px',
        height: '65px',
      }}
    >
      {navigationItems.map(({
        icon: Icon,
        labelKey,
        to,
      }) => (
        <BottomNavigationAction
          component={Link}
          icon={<Icon />}
          key={to}
          label={t(labelKey)}
          nativeButton={false}
          to={to}
          value={to}
        />
      ))}
    </BottomNavigation>
  );
}
