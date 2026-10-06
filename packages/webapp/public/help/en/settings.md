# Settings

Everything that only concerns Lauschkiste itself is set in the web app. Changes are saved right away; some take effect only after Lauschkiste restarts, then "Restart now" appears at the top. That restarts only the Lauschkiste service, not the whole box.

| Page | Content |
| --- | --- |
| Status | version, IP address, storage, temperature, battery |
| Playback & audio | outputs (name, device, volume limit), volume, player, audiobooks, podcasts, startup and shutdown sound, keys of USB devices and media keys |
| Cards | card list, placing the same card again, readers (delay, place instead of swipe, action when the card is taken off) |
| Library | covers, scanning, network drive (Samba) |
| Plugins | switch extensions on and off and set them up, e.g. Raspberry Pi (GPIO buttons, rotary encoders, LED, battery) |
| System | announcements, restart, shut down |

## Plugins

Plugins add hardware and sources to Lauschkiste. Switching them on or off takes effect after a restart. If a plugin misses packages, "Install" on the plugins page installs them; that can take a few minutes.

## What only works on the box

Settings of the operating system need administrator rights and are made with `lauschctl setup` on the box: sound card, installing Samba, WiFi hotspot, boot optimisation, kiosk mode, setting up the reader. See [Commands on the box](/help/lauschctl).
