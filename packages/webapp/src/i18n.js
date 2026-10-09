import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';

// Based on https://dev.to/adrai/how-to-properly-internationalize-a-react-application-using-i18next-3hdb
const i18nReady = i18n
  // i18next-http-backend
  // loads translations from your server
  // https://github.com/i18next/i18next-http-backend
  .use(Backend)
  // detect user language
  // learn more: https://github.com/i18next/i18next-browser-languageDetector
  .use(LanguageDetector)
  // pass the i18n instance to react-i18next.
  .use(initReactI18next)
  // init i18next
  // for all options read: https://www.i18next.com/overview/configuration-options
  .init({
    // A browser may still hold translations of whatever else was served from this address before
    // (an older version, another program); a new build id makes it fetch them again.
    backend: { queryStringParams: { v: import.meta.env.VITE_BUILD_ID } },
    debug: import.meta.env.DEV,
    // lng: 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // not needed for react as it escapes by default
    },
    react: {
      // plugins' texts are added after the start
      bindI18nStore: 'added',
      useSuspense: false,
    },
  });

// Plugins bring their own texts (names, the labels and help of their settings); the web app's own win, and a
// language a plugin lacks falls back to English and then to the plugin's English schema texts.
const loadPluginTexts = async (language) => {
  const base = String(language || '').split('-')[0].toLowerCase();
  await Promise.all([...new Set([base, 'en'])].filter(Boolean).map(async (code) => {
    try {
      const response = await fetch(`/api/v1/translations/${code}`);
      if (!response.ok) return;
      i18n.addResourceBundle(code, 'translation', await response.json(), true, false);
    }
    catch {
      // the plugins' texts are optional
    }
  }));
};

i18nReady.then(() => loadPluginTexts(i18n.resolvedLanguage || i18n.language));
i18n.on('languageChanged', loadPluginTexts);

export { i18nReady };
export default i18n;
