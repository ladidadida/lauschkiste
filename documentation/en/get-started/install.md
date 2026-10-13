# Install

This takes about half an hour, most of it waiting. Every step says what you should see when it worked. This page describes a Raspberry Pi; on a PC or laptop see
[On a PC, laptop or mini PC](other-computers.md).

## 1. Write the SD card

1. Download the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) and start it.
2. Choose your Pi model and the system **Raspberry Pi OS Lite** (64 bit). "Lite" means no desktop, which is what the
   box wants.
3. Choose the SD card and click next. When it asks for customisation, choose **Edit settings** and enter:
   - a **name** for the box (for example `lauschkiste`),
   - a **user name and password** (write them down),
   - your **WiFi** name and password,
   - and under *Services* switch on **SSH** with password.
4. Write the card. Put it into the Pi, connect the power and wait about two minutes.

## 2. Log in to the box

Open a terminal on your computer (on Windows: *PowerShell*) and type, with your user name and the box's name:

```bash
ssh <user>@<name>.local
```

Answer *yes* when it asks about the fingerprint, then type your password. You see a prompt such as
`pi@lauschkiste:~ $`. If the name is not found, look up the box's address in your router and use that instead of
`<name>.local`.

## 3. Install

Paste this line and press Enter:

```bash
curl -fsSL https://raw.githubusercontent.com/ladidadida/lauschkiste/main/install.sh | bash
```

It installs a few base packages and Lauschkiste itself. At the end it says *Lauschkiste is installed*. Open a new shell
(or type `source ~/.profile`) so the new commands are found.

## 4. Set up the box

```bash
lauschctl setup
```

`lauschctl setup` asks a few questions, one after the other. Press Enter to accept the suggestion in brackets. If you
are not sure, accept it: you can run `lauschctl setup` again at any time to change something. If the connection is
unreliable, run it in `screen` or `tmux`.

| Question | What to answer |
| --- | --- |
| What kind of machine is this? | *Raspberry Pi* on a Pi. On a computer: [On a PC, laptop or mini PC](other-computers.md). |
| Upgrade all operating system packages now | *No* is fine for a first try. |
| Which sound card sits on the header | If you plugged a sound card onto the Pi, pick it (HiFiBerry boards are recognised). Otherwise *none*. |
| Use 'Pimoroni pHAT BEAT' / 'Power button' / 'Battery' / 'GPIO buttons and knobs'? | *No*, unless you have them. These come after the questions about the box itself, together with your own hardware plugins. |
| Start Lauschkiste at boot, without anyone logging in | *Yes*. The box then starts by itself when you plug it in. |
| Serve the web app on port 80 | *Yes*. The address is then just `http://<name>.local`. |
| Configure an RFID reader now | *Yes*, and choose your reader. A USB reader is the simplest. See [RFID readers](../hardware/readers.md). |
| Share the library on the network with Samba | *No* for now. You can upload music in the web page; see [Music](../using/music.md). |
| Show the web app on an attached display | *No*, unless you attached a screen: [A screen on the box](../hardware/screen.md). |
| WiFi hotspot when no known WiFi is in range | *No* for now: [Away from home](../using/wifi-hotspot.md). |
| Quiet boot | *No*. It only hides boot messages. |

Some steps change the boot configuration. At the end `lauschctl setup` tells you if a restart is needed:

```bash
sudo reboot
```

## 5. Check

Wait a minute, then open `http://<name>.local` in a browser on your computer or phone. You should see the Lauschkiste
web page with the player. If you did not choose port 80, add `:5556` to the address.

If it does not work, run `lauschctl setup --check`: it lists what is missing. More in
[When something does not work](../maintenance/troubleshooting.md).

Next: [The box is running: what now?](first-steps.md).
