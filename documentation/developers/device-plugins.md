# Device plugins (plan)

Status: a plan, not implemented. What exists today is described in [Hardware](hardware.md), where the device plugin is
still called a *board* plugin.

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
| **Device plugin** | describes the machine: what it provides, how it is detected, what setup offers for it | `device_raspberry_pi`, `device_pc` |
| **Peripheral plugin** | hardware attached to the machine, independent of which machine | `gpio_controls`, `battery`, `power_button`, `phat_beat`, RFID readers |
| Core module | always there; may still ask the device what it may do | `display`, `hardware` |

The peripheral plugins are today called "device plugins" in the code and the documentation (and the package
`lauschkiste-plugin-devices`); they are renamed to avoid two meanings.

## The setup starts with the device

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
  Lauschkiste do to it, for example `system_setup` (may change boot and network configuration), `autologin`, `backlight`.
- `detect(read)`: recognises the machine; only suggests, never enables silently.
- **Setup steps and questions**: the device contributes the steps that only make sense on it (boot configuration, quiet
  boot, WiFi hotspot, kiosk), each with its own defaults. A device that provides no `system_setup` offers none of them.
- Shutdown and reboot, if the machine should be switched off by a box (a laptop does not provide `poweroff`).

The `device_pc` plugin, for ordinary x86/arm computers, is deliberately modest: it provides almost nothing and changes
nothing outside Lauschkiste. Someone who dedicates a mini PC to the box may later get a second plugin with more.

## Compatibility checks

Plugins and core modules keep `needs` for capabilities. Two additions:

- `compatible(device) -> Optional[str]`: a check for what only the module knows ("needs NetworkManager", "needs a
  controllable backlight"). It returns `None` or the reason as plain text.
- The result is the same everywhere: setup does not ask the question, the web app greys the switch out and shows the
  reason, `lauschctl plugin enable` refuses, and a config that enables it anyway skips it at startup with the problem
  listed (all as for a missing `needs` today).

## Order of work

1. Rename board to device in the plugin contract (`provides 'device'`, the `hardware.boards` extension point) and the
   peripheral plugins' name, with the documentation.
2. `compatible()` and the new capabilities; `display` and the kiosk step ask the device first. These are the places where
   an ordinary computer would be changed against its owner's will today.
3. The device as the first setup step, with the choice of an own plugin; the device contributes steps.
4. `device_pc`.
