# Update

- [Updating Lauschkiste](#updating-lauschkiste)
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
and is not touched by an update.

## Migration path from Phoniebox 2

There is no update path from Phoniebox 2.x. Install Lauschkiste on a fresh Raspberry Pi OS image,
see [Installation](./installation.md).

> [!IMPORTANT]
> Do start with a fresh SD card image!
