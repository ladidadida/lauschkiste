import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

const page = (slug, en, de) => ({ slug, label: en, translations: { de } });
const group = (en, de, items) => ({ label: en, translations: { de }, items });

export default defineConfig({
  site: 'https://ladidadida.github.io',
  base: '/lauschkiste',
  redirects: { '/': '/lauschkiste/en/' },
  integrations: [
    starlight({
      title: 'Lauschkiste',
      logo: { src: './src/assets/logo.svg', alt: 'Lauschkiste' },
      customCss: ['./src/styles.css'],
      defaultLocale: 'en',
      locales: {
        en: { label: 'English', lang: 'en' },
        de: { label: 'Deutsch', lang: 'de' },
      },
      social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/ladidadida/lauschkiste' }],
      editLink: { baseUrl: 'https://github.com/ladidadida/lauschkiste/edit/main/documentation/' },
      sidebar: [
        group('Get started', 'Einstieg', [
          page('get-started/what-you-need', 'What you need', 'Was du brauchst'),
          page('get-started/install', 'Install', 'Installieren'),
          page('get-started/other-computers', 'On a PC or laptop', 'Auf PC oder Laptop'),
          page('get-started/first-steps', 'The box is running', 'Die Box läuft'),
          page('get-started/first-card', 'Your first card', 'Deine erste Karte'),
          page('what-next', 'What next?', 'Was als Nächstes?'),
        ]),
        group('Using the box', 'Die Box benutzen', [
          page('using/music', 'Music and the library', 'Musik und Bibliothek'),
          page('using/cards', 'Cards', 'Karten'),
          page('using/audiobooks', 'Audiobooks', 'Hörbücher'),
          page('using/podcasts', 'Podcasts', 'Podcasts'),
          page('using/radio', 'Radio', 'Radio'),
          page('using/time-limits', 'Time limits', 'Zeitlimits'),
          page('using/sound', 'Sound and Bluetooth', 'Ton und Bluetooth'),
          page('using/wifi-hotspot', 'Away from home', 'Unterwegs'),
        ]),
        group('Hardware', 'Hardware', [
          page('hardware/readers', 'RFID readers and cards', 'RFID-Leser und Karten'),
          page('hardware/sound-cards', 'Sound cards and amplifiers', 'Soundkarten und Verstärker'),
          page('hardware/buttons', 'Buttons and knobs', 'Tasten und Drehregler'),
          page('hardware/power', 'Power button and battery', 'Ein-Aus-Taste und Akku'),
          page('hardware/screen', 'A screen on the box', 'Ein Bildschirm an der Box'),
        ]),
        group('Looking after the box', 'Die Box pflegen', [
          page('maintenance/update-uninstall', 'Updating and removing', 'Aktualisieren und entfernen'),
          page('maintenance/troubleshooting', 'When something does not work', 'Wenn etwas nicht klappt'),
          page('maintenance/configuration', 'Settings and files', 'Einstellungen und Dateien'),
          page('maintenance/commands', 'The commands', 'Die Befehle'),
          page('maintenance/how-it-works', 'How it works', 'Wie es funktioniert'),
        ]),
        group('For developers (English)', 'Für Entwickler (Englisch)', [
          { slug: 'developers', label: 'Overview', translations: { de: 'Übersicht' } },
          { autogenerate: { directory: 'developers' } },
        ]),
      ],
    }),
  ],
});
