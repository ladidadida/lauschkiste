# Update

- [Updating Lauschkiste](#updating-lauschkiste)
- [Coming from an installation before the renaming](#coming-from-an-installation-before-the-renaming)
- [Coming from an installation with the old installer](#coming-from-an-installation-with-the-old-installer)
- [Migration path from Phoniebox 2](#migration-path-from-phoniebox-2)

## Updating Lauschkiste

```bash
lauschctl update --check     # is there a newer version?
lauschctl update             # install it, re-apply the setup, restart Lauschkiste
```

- **Package installation** (the default of `install.sh`): installs the latest release from
  GitHub (`--version vX.Y.Z` for a specific one) into Lauschkiste's environment. Plugins you
  installed yourself stay, extra dependencies of enabled plugins are kept.
- **Source installation** (`install.sh --source`): `git pull` of the current branch, then
  `uv sync`; the web app is rebuilt if it changed and `npm` is installed.

Afterwards `lauschctl setup --yes` re-applies the setup with your earlier answers (e.g. an updated
service definition) and a running Lauschkiste service is restarted.

Your data -- music, settings, cards -- lives in the Lauschkiste home (`lauschctl home` shows it)
and is not touched by an update. Cards in the old format are converted when Lauschkiste starts
(with a backup of the card database).

## Coming from an installation before the renaming

Lauschkiste was called "jukebox" before version 0.1 (commands `jukebox run` / `jukebox setup`,
service `jukebox-daemon`, data in `~/jukebox`). Such installations keep working:

- Run `install.sh` again (or `jukebox update`, which still exists for one release). The data
  directory `~/jukebox` (and `settings/jukebox.yaml`, `JUKEBOX_HOME`) stays in use.
- `lauschctl setup` replaces the `jukebox-daemon` service with `lauschkiste`, and recognizes the
  blocks it added to system files before, so nothing is added twice.
- The `jukebox` command still works for one release; use `lauschkiste` and `lauschctl` instead.

## Coming from an installation with the old installer

Installations made with the old `install-jukebox.sh` keep their data in
`~/RPi-Jukebox-RFID/shared`. Either keep using that checkout as a source installation:

```bash
cd ~/RPi-Jukebox-RFID && git remote set-url origin https://github.com/ladidadida/lauschkiste.git && git pull
curl -fsSL https://raw.githubusercontent.com/ladidadida/lauschkiste/main/install.sh | bash -s -- --source ~/RPi-Jukebox-RFID
```

or install the package and point it at the old data:

```bash
curl -fsSL https://raw.githubusercontent.com/ladidadida/lauschkiste/main/install.sh | bash -s -- --home ~/RPi-Jukebox-RFID/shared
```

Paths written by the old installer (`../../shared/...`) are understood. The old service
(`/usr/lib/systemd/user/jukebox-daemon.service`) is replaced by `lauschkiste.service`, which
`lauschctl setup` writes to `~/.config/systemd/user/`.

## Migration path from Phoniebox 2

There is no update path from Phoniebox 2.x. Install Lauschkiste on a fresh Raspberry Pi OS image,
see [Installation](./installation.md).

> [!IMPORTANT]
> Do start with a fresh SD card image!
