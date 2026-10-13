# Device plugins

Status: implemented except for what is listed under *Not done yet*. Hardware details are in [Hardware](hardware.md).

## The idea

Lauschkiste runs on a Raspberry Pi, on an old laptop, on a mini PC, in the future on other single-board computers. The
**device plugin** says which of these it is, and everything else depends on it: which setup questions are asked, which
system changes are allowed, which plugins and settings make sense. The core and the other plugins do not ask "is this a
Raspberry Pi?"; they ask the device what it provides.

A laptop is not a board, so the name is *device*, not *board*. The shorter word also fits what it is: the machine the box
runs on.

## Terms

| Term | Meaning | Examples |
| --- | --- | --- |
| **Device plugin** | describes the machine: what it provides, how it is detected, what setup offers for it | `device_raspberry_pi`, `device_pc_test` |
| **Peripheral plugin** | hardware attached to the machine, independent of which machine | `gpio_controls`, `battery`, `power_button`, `phat_beat`, RFID readers |
| Core module | always there; may still ask the device what it may do | `display`, `hardware` |

The peripheral plugins used to be called "device plugins" (package `lauschkiste-plugin-devices`, now
`lauschkiste-plugin-peripherals`); they were renamed to avoid two meanings.

## The setup, step by step

`lauschctl setup` runs in two parts, and the questions come in this order:

1. **The device** is recognised or chosen (`device`), or installed: the choices are the installed device plugins, *a device
   plugin of my own* and *none*.
2. **The device's options**: the questions the device allows (system packages, sound card on the header, service and
   port 80, audio outputs, Samba, kiosk, hotspot, quiet boot, login message).
3. **The peripherals** are proposed and installed (`extra_plugins` installs plugins of other sources, `peripherals`
   proposes every installed plugin with `setup_kind = 'peripheral'` that fits the device, third-party ones included).
4. **The peripherals' options**: `peripheral_options` asks the settings of a peripheral that are marked for the setup
   (`json_schema_extra={'setup': ...}`, e.g. the battery sensor), and `rfid` configures the reader. The boot
   configuration (`raspi`) is written last because it follows from everything chosen.

Details of the first part:

1. `lauschctl setup` first asks which device this is. The list holds every installed device plugin, the detected one is
   preselected (`detect()`), and **none / unknown** is a choice.
2. A user can name **their own device plugin** right there (package name, `github:owner/repo[@tag]` or a URL, the way
   *Plugins from other sources* works today). It is installed and used like a bundled one. Third-party device plugins are
   an intended case, not an exception.
3. Everything after depends on the choice: the device contributes its setup steps and questions, and states what the
   machine allows. The CLI no longer contains device knowledge such as `is_raspberry_pi()`.
4. Only then come the plugins. Each one checks *"am I compatible with this device?"* and is offered, hidden or greyed out
   with its reason.

## What a device plugin provides

- `provides`: capabilities, as today (`gpio`, `i2c`, `spi`, `poweroff`, ...). New ones describe what the machine lets
  Lauschkiste do to it, for example `system_setup` (may change boot and network configuration), `autologin`, `screen`.
- `detect(read)`: recognises the machine; only suggests, never enables silently.
- **What the setup offers**: the plugin brings its own steps with `setup_steps()` (`lauschkiste_cli.setup.base.Step`
  objects; the method imports the CLI itself, because the service runs without it). `device_raspberry_pi` brings the
  sound card, the quiet boot and the boot configuration. Generic steps that many devices can use (port 80, Samba, WiFi
  hotspot, kiosk, login message) stay in the CLI and are tied to capabilities; a device that provides no `system_setup`
  offers none of them. A step has `position`: `early` (asked right after the device, with its options) or `late`
  (run after everything chosen, like the boot configuration).
- Shutdown and reboot, if the machine should be switched off by a box (a laptop does not provide `poweroff`).

Ordinary computers have two device plugins, in one package: `device_pc_test` is deliberately modest and changes nothing
outside Lauschkiste (a work computer, a quick try); `device_pc_box` is for a computer that is a box of its own and
may be set up for that (port 80, Samba, console login, kiosk). Only the test one is ever detected, so a computer is
never set up as a box by accident.

## Compatibility checks

Every module, core or plugin, can declare `needs` (capabilities that the enabled plugins must provide) and override
`compatible(provided) -> Optional[str]` for what only the module knows ("needs NetworkManager", "needs a
controllable backlight"); it returns `None` or the reason as plain text. `provided` holds the capabilities of the enabled
plugins, the device plugin's among them.

- A plugin that fails the check is not started and is listed with the reason; the web app greys the switch out and shows
  it, `lauschctl plugin enable` refuses, and a config that enables it anyway skips it with the problem listed.
- A core module that fails is not started either (`display` needs `screen`); the daemon still runs.
- Setup steps and questions carry the same `needs`; what the device does not provide is not asked and not run.

## Capabilities of the bundled devices

| Capability | Meaning | `device_raspberry_pi` | `device_pc_box` | `device_pc_test` |
| --- | --- | --- | --- | --- |
| `device` | this is the device (only one) | yes | yes | yes |
| `gpio`, `i2c`, `spi`, `i2s`, `uart`, `poweroff` | pins, buses, switching the machine off | yes | no | no |
| `boot_config` | Lauschkiste may write the boot configuration (Raspberry Pi's `config.txt`) | yes | no | no |
| `system_setup` | Lauschkiste may change the system: port 80, hotspot, Samba, login message, upgrades | yes | yes | no |
| `autologin` | console autologin may be set (kiosk) | yes | yes | no |
| `screen` | the screen may be switched off and used as a kiosk | yes | yes | no |

## What was done

- `board` became `device` everywhere (`provides 'device'`, `hardware.devices`, `GET /api/v1/hardware` field `device`);
  today's hardware plugins are `peripherals`. Contract 3.0, `hardware` 2.0.
- `lauschctl setup` starts with the device step, then the device's options, then the peripherals and their options; the CLI no longer contains `is_raspberry_pi()`. The choices are the
  installed device plugins, *a device plugin of my own* (package, `github:owner/repo[@tag]` or URL, installed like
  *Plugins from other sources*) and *none*.
- `device_pc_test` and `device_pc_box` for ordinary computers.
- `lauschctl update` replaces the old packages (`lauschkiste-plugin-board-raspberry-pi`, `-devices`; the removed
  `-mpd`) and renames `board_raspberry_pi` in the configuration to `device_raspberry_pi`.

- A device plugin brings setup steps (`Plugin.setup_steps()`, contract 3.2); the steps of the Raspberry Pi
  (`hardware`, `boot`, `raspi`) moved from the CLI into `device_raspberry_pi`. `lauschctl setup raspi` on another device
  says the step does not apply.

## Not done yet

- `device_pc_box` brings no steps of its own yet; the generic ones in the CLI (hotspot, kiosk, ...) could move into
  plugins or be shared as building blocks, once a second device really needs different ones.
- Shutdown and reboot for `device_pc_box` (it provides no `poweroff` yet).
- `lauschctl setup --check` still asks the questions; it should only report.
