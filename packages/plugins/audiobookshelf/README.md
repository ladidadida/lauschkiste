# lauschkiste-plugin-audiobookshelf

Audiobooks from an [Audiobookshelf](https://www.audiobookshelf.org) server. A plugin for [Lauschkiste](https://github.com/ladidadida/lauschkiste), an open-source RFID audio player for kids.

The books of the server show up in the Audiobooks tab next to the local ones and stream from the server;
the position is shared with the Audiobookshelf apps.

Install it next to [`lauschkiste`](https://pypi.org/project/lauschkiste/) (same version), then
switch it on in the web app (Settings → Plugins) or with:

```bash
lauschctl plugin enable audiobookshelf
```

Enter the server address and an API key (Audiobookshelf: Settings → API Keys) in its settings.

Documentation: [for builders](https://github.com/ladidadida/lauschkiste/blob/main/documentation/builders/README.md). MIT license.
