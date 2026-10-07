# Renaming to Lauschkiste

> Plan for track 4 of [roadmap-core-architecture.md](roadmap-core-architecture.md) ("New name").
> Status: steps 1-6 done (2026-10-04); open: archive the fork, first pre-release, verification on a Pi.

## Decision

- Name: **Lauschkiste** (German *lauschen*, to listen closely; *die Kiste*, the box). Tagline in
  English: *Lauschkiste - an open-source RFID audio player for kids*.
- Main domain `lauschkiste.org`; other endings (`.de`, `.io`) only as redirects.
- A new, standalone GitHub repository [`ladidadida/lauschkiste`](https://github.com/ladidadida/lauschkiste)
  with the full history of the fork (created 2026-10-01); the fork is archived with a pointer to
  the new repository. The MIT license keeps the original copyright
  notice; the README names Phoniebox as origin.

## Naming scheme

| What | Now | New |
| --- | --- | --- |
| Core distribution / import package | `jukebox` / `jukebox` | `lauschkiste-core` / `lauschkiste` |
| CLI distribution / import package | `jukebox-cli` / `jukebox_cli` | `lauschkiste` / `lauschkiste_cli` (what users install) |
| Bundled plugins | `jukebox-plugin-<name>`, `jukebox_rfid_readers`, `jukebox_plugin_*` | `lauschkiste-plugin-<name>`, `lauschkiste_plugin_<name>` |
| Plugin entry-point group | `jukebox.plugins` | `lauschkiste.plugins` |
| Commands | `jukebox run`; `jukebox setup`, `plugin`, `update`, `home`, `debug` | server: `lauschkiste` (what `jukebox run` is now, started by the service); management: `lauschctl setup`, `lauschctl plugin ...`, `lauschctl update`, `lauschctl home`, `lauschctl debug ...` |
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

None: there were no users yet, so Lauschkiste does not know the old names at all (no fallbacks
for `JUKEBOX_*`, `~/jukebox`, `jukebox.yaml`, the `jukebox-daemon` service or `jb.*` loggers).
Support for people moving over from a Phoniebox can be built later if needed.

## Versioning

- Plugins import `lauschkiste.contract` instead of `jukebox.contract`: the framework contract
  becomes **2.0**; module interface versions stay (their actions and events do not change).
- Versions start over at 0: all packages (core, CLI, bundled plugins) become `0.1.0a1` (PEP 440);
  the first pre-release is tagged `v0.1.0-alpha.1`. Tags of upstream Phoniebox releases are not carried over.

## Steps

Each step leaves the tests green and is one commit.

1. **Packages and imports:** `git mv` the package directories, rename distributions, imports,
   entry-point group and module references (mechanical, scripted with word boundaries, then
   reviewed). Regenerate interface snapshots, contract 2.0.
2. **Runtime names:** environment variables, home directory, configuration file name, logger
   names, unit name, Samba share, login message, hotspot SSID; the compatibility fallbacks above
   with tests.
3. **Command line:** two console scripts from the CLI package: `lauschkiste` (server, the options of
   `jukebox run`) and `lauschctl` (all other commands); help texts.
4. **Web app:** title, manifest, translations, texts mentioning Phoniebox; logo/icons later.
5. **Installer and CI:** `install.sh` (repository, paths, messages), `DEFAULT_REPO`, workflows,
   `ci/` scripts, Docker files.
6. **Documentation:** README (name, tagline, origin and credits, pronunciation), AGENTS.md,
   builder and developer docs. Historic documents (roadmap history, changelog) keep the old names
   where they describe the past.
7. **Repository:** the new repository exists (step done early); archive the fork with a pointer. Then the first pre-release `v0.1.0-alpha.1` (wheels via the existing workflow).
8. **Verification:** install the pre-release with `install.sh` on the test Pi (fresh and as an
   upgrade of the existing test install), full test pass as in the Pi test plan.

## Open questions

- Trademark check (DPMA/EUIPO) and domain registration (by the maintainer).
- Logo and icons for the web app.
