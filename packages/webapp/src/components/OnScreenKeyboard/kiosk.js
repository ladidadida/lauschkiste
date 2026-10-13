const KEY = 'lauschkiste.kiosk';

// The display attached to the box opens the web app with `?kiosk`; the browser remembers it for later visits.
export const isKiosk = () => {
  try {
    if (new URLSearchParams(window.location.search).has('kiosk')) window.localStorage.setItem(KEY, '1');
    return window.localStorage.getItem(KEY) === '1';
  } catch {
    return false;
  }
};
