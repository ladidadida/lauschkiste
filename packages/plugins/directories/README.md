# lauschkiste-plugin-directories

Find podcasts and radio stations and add them with one tap: podcasts in Apple Podcasts, fyyd and (with a key) the Podcast Index, radio stations in radio-browser.info. Two plugins of [Lauschkiste](https://github.com/ladidadida/lauschkiste), an open-source RFID audio player for kids: `podcast_directories` and `radio_directories`.

Install it next to [`lauschkiste`](https://pypi.org/project/lauschkiste/) (same version), then
switch the plugins on in the web app (Settings → Plugins) or with:

```bash
lauschctl plugin enable podcast_directories
lauschctl plugin enable radio_directories
```

Every directory can be switched off in the settings. Searches go to the directories you leave on.

Documentation: [for builders](https://github.com/ladidadida/lauschkiste/blob/main/documentation/builders/README.md). MIT license.
