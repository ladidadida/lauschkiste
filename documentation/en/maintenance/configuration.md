# Settings and files

Most things you set in the web page (Settings). A few things change the operating system and are done on the box with
`lauschctl` ([commands](commands.md)). The rest is in files.

## Where everything is

All data of the box is in one folder, the *Lauschkiste home*. `lauschctl home` prints it. On a Raspberry Pi it is
`~/lauschkiste`.

```text
~/lauschkiste/
├── settings/    lauschkiste.yaml (settings), cards.yaml, rfid.yaml, secrets.yaml, logger.yaml
├── library/     music/ and audiobooks/
├── playlists/
├── logs/
└── cache/       cover pictures, downloads
```

To back the box up, copy this folder.

## Change a single setting

```bash
lauschctl config get volume.soft_max_volume
lauschctl config set volume.soft_max_volume 60
```

Keys and passwords of plugins (such as the Audiobookshelf key) are kept apart in `secrets.yaml`, readable only by the
box's user: `lauschctl config set <key> --secret`. `lauschctl config get` does not show them.

## Edit the file

The file `settings/lauschkiste.yaml` is commented. Stop Lauschkiste before you edit it, so it does not overwrite your
change:

```bash
systemctl --user stop lauschkiste
nano ~/lauschkiste/settings/lauschkiste.yaml
systemctl --user start lauschkiste
```

Relative paths in the files are relative to the Lauschkiste home; absolute paths and paths starting with `~/` are used
as given.

## Try a different configuration

```bash
lauschkiste --conf /path/to/other.yaml
```

starts Lauschkiste in the console with another file, for example to test a lower maximum volume.

## Plugins

A plugin adds functions: board support, buttons, readers, directories for podcasts and radio. It only runs when it is
switched on, under Settings → Plugins or with `lauschctl plugin enable <name>`.

```bash
lauschctl plugin list                      # installed plugins and whether they run
lauschctl plugin enable <name>
lauschctl plugin disable <name>
lauschctl plugin install <package>         # a plugin from PyPI or another source
```

Install only plugins you trust: a plugin runs with the rights of the box's user.
