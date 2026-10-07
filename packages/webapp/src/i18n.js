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
      useSuspense: false,
    },
  });

export { i18nReady };
export default i18n;
