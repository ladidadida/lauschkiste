import { createTheme } from '@mui/material/styles';

// What a theme file (a CSS file with these custom properties on :root) provides; used where it leaves one out.
const DEFAULTS = {
  accent: '#4db6ac',
  'accent-text': '#06201d',
  background: '#101418',
  font: 'system-ui, sans-serif',
  mode: 'dark',
  muted: '#9aa7b2',
  radius: '18px',
  surface: '#1b2229',
  text: '#f2f5f7',
};

const TEXT_SIZES = { normal: 16, large: 20, huge: 26 };

const themeUrl = (name) => `/api/v1/kiosk_standard/themes/${encodeURIComponent(name)}.css`;

const readVariables = () => {
  const style = getComputedStyle(document.documentElement);
  return Object.fromEntries(Object.entries(DEFAULTS).map(([key, fallback]) => (
    [key, style.getPropertyValue(`--kiosk-${key}`).trim() || fallback]
  )));
};

const kioskTheme = (variables, textSize = 'large') => createTheme({
  palette: {
    mode: variables.mode === 'light' ? 'light' : 'dark',
    primary: { main: variables.accent, contrastText: variables['accent-text'] },
    background: { default: variables.background, paper: variables.surface },
    text: { primary: variables.text, secondary: variables.muted },
  },
  shape: { borderRadius: parseInt(variables.radius, 10) || 18 },
  typography: { fontFamily: variables.font },
  components: {
    MuiSlider: {
      styleOverrides: {
        root: { height: 10, padding: '20px 0' },
        thumb: { height: 30, width: 30 },
      },
    },
    MuiCssBaseline: {
      styleOverrides: {
        html: { fontSize: `${TEXT_SIZES[textSize] || TEXT_SIZES.large}px` },
        body: { overscrollBehavior: 'none', userSelect: 'none', WebkitTapHighlightColor: 'transparent' },
      },
    },
  },
});

export { DEFAULTS, TEXT_SIZES, kioskTheme, readVariables, themeUrl };
