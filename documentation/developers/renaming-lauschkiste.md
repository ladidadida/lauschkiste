# Renaming to Lauschkiste

> Plan for track 4 of [roadmap-core-architecture.md](roadmap-core-architecture.md) ("New name").
> Status: planned, to be done after the Raspberry Pi 3B test of
> [packaging-and-setup.md](packaging-and-setup.md).

## Decision

- Name: **Lauschkiste** (German *lauschen*, to listen closely; *die Kiste*, the box). Tagline in
  English: *Lauschkiste - an open-source RFID audio player for kids*.
- Main domain `lauschkiste.org`; other endings (`.de`, `.io`) only as redirects.
- A new, standalone GitHub repository `lauschkiste` with the full history of this fork; the fork is
  archived with a pointer to the new repository. The MIT license keeps the original copyright
  notice; the README names Phoniebox as origin.

## Naming scheme

| What | Now | New |
| --- | --- | --- |
| Core distribution / import package | `jukebox` / `jukebox` | `lauschkiste` / `lauschkiste` |
| CLI distribution / import package | `jukebox-cli` / `jukebox_cli` | `lauschkiste-cli` / `lauschkiste_cli` |
| Bundled plugins | `jukebox-plugin-<name>`, `jukebox_rfid_readers`, `jukebox_plugin_*` | `lauschkiste-plugin-<name>`, `lauschkiste_plugin_<name>` |
| Plugin entry-point group | `jukebox.plugins` | `lauschkiste.plugins` |
| Command | `jukebox run`, `jukebox setup`, ... | `lauschkiste ...` (open: short alias `lausch`) |
| Environment | `JUKEBOX_HOME`, `JUKEBOX_CONF`, `JUKEBOX_LOGGER_CONF`, `JUKEBOX_WEBAPP_DIR`, `JUKEBOX_REPO`, `JUKEBOX_STRICT` | `LAUSCHKISTE_*` |
| Home directory | `$XDG_DATA_HOME/jukebox`, on a Pi `~/jukebox` | `$XDG_DATA_HOME/lauschkiste`, on a Pi `~/lauschkiste` |
| Main configuration | `settings/jukebox.yaml` | `settings/lauschkiste.yaml` |
| systemd user unit | `jukebox-daemon.service` | `lauschkiste.service` |
| Logger names | `jb.*` | `lauschkiste.*` |
| Web app title / manifest | "Phoniebox", "Phoniebox RFID Jukebox" | "Lauschkiste" |
| Samba share, login message, hotspot SSID | `jukebox`, `99-rpi-jukebox-rfid-welcome`, `Phoniebox_Hotspot_<host>` | `lauschkiste`, `99-lauschkiste-welcome`, `Lauschkiste_<host>` |
| Repository | `ladidadida/RPi-Jukebox-RFID` | `ladidadida/lauschkiste` |

The REST paths (`/api/v1/...`), event topics and card action ids (`player.play_folder`, ...) do not
contain the name and stay as they are, so cards, the web app and API clients are unaffected.

## Existing installations

Only test installations of this fork exist, so compatibility is kept small and temporary (one
release, then removed):

- `LAUSCHKISTE_HOME` falls back to `JUKEBOX_HOME`; the default home falls back to an existing
  `~/jukebox` / `$XDG_DATA_HOME/jukebox`.
- `settings/lauschkiste.yaml` falls back to an existing `settings/jukebox.yaml`.
- `lauschkiste setup` (service step) disables and removes `jukebox-daemon.service` when it finds it.
- Configurations from upstream Phoniebox installs keep working as today (paths below `shared/`).

## Versioning

- Plugins import `lauschkiste.contract` instead of `jukebox.contract`: the framework contract
  becomes **2.0**; module interface versions stay (their actions and events do not change).
- Package version: the first release of the new name is `4.0.0-alpha.1` (tag `v4.0.0-alpha.1`),
  continuing the version line of the code base (open, see below).

## Steps

Each step leaves the tests green and is one commit.

1. **Packages and imports:** `git mv` the package directories, rename distributions, imports,
   entry-point group and module references (mechanical, scripted with word boundaries, then
   reviewed). Regenerate interface snapshots, contract 2.0.
2. **Runtime names:** environment variables, home directory, configuration file name, logger
   names, unit name, Samba share, login message, hotspot SSID; the compatibility fallbacks above
   with tests.
3. **Command line:** `lauschkiste` command (and the alias, if decided), help texts.
4. **Web app:** title, manifest, translations, texts mentioning Phoniebox; logo/icons later.
5. **Installer and CI:** `install.sh` (repository, paths, messages), `DEFAULT_REPO`, workflows,
   `ci/` scripts, Docker files.
6. **Documentation:** README (name, tagline, origin and credits, pronunciation), AGENTS.md,
   builder and developer docs. Historic documents (roadmap history, changelog) keep the old names
   where they describe the past.
7. **Repository:** new repository with full history, `main` = this branch; tags; archive the fork
   with a pointer. Then the first pre-release `v4.0.0-alpha.1` (wheels via the existing workflow).
8. **Verification:** install the pre-release with `install.sh` on the test Pi (fresh and as an
   upgrade of the existing test install), full test pass as in the Pi test plan.

## Open questions

- Short command alias `lausch` in addition to `lauschkiste`?
- Version line: continue at 4.0.0, or start the new name at 1.0.0 / 0.x?
- Trademark check (DPMA/EUIPO) and domain registration (by the maintainer).
- Logo and icons for the web app.
