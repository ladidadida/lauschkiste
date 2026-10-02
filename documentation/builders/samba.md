# Samba

Samba makes the library a network drive in Windows Explorer, the macOS Finder or a Linux file
manager. It is optional and off by default: the web app can upload music too, see
[Copying music](copying-music.md).

## Enable

```bash
lauschctl setup samba
```

The step installs Samba and shares the library (`library` in the Lauschkiste home, with `music` and `audiobooks`) as
`lauschkiste`. Settings, the card database and logs are not shared. The first time, it asks for a
Samba password (at least 8 characters) for your user; with `--yes` and no password set yet, the
step is skipped until you run it interactively.

## Connect

Open your network environment and select your Lauschkiste, or enter the address directly:

* Windows: `\\<ip-address-of-your-lauschkiste>\lauschkiste`
* macOS: `smb://<ip-address-of-your-lauschkiste>/lauschkiste` (Finder: Go, Connect to Server),
  see also [Apple's guide](https://support.apple.com/guide/mac-help/mchlp1140/mac)
* Linux: `smb://<ip-address-of-your-lauschkiste>/lauschkiste`

Log in with your user name on the Pi and the Samba password.

## Change the password

```bash
sudo smbpasswd -a <your-username>
```
