# Samba

Samba makes the music folder a network drive in Windows Explorer, the macOS Finder or a Linux file
manager. It is optional and off by default: the web app and SFTP can copy music too, see
[Copying music](copying-music.md).

## Enable

```bash
lauschctl setup samba
```

The step installs Samba and shares the music folder (`audiofolders` in the Lauschkiste home) as
`lauschkiste`. Settings, the card database and logs are not shared. The first time, it asks for a
Samba password (at least 8 characters) for your user; with `--yes` and no password set yet, the
step is skipped until you run it interactively.

Installations from before version 0.1 shared the whole home directory with the password
`raspberry`. Running `lauschctl setup samba` again limits the share to the music folder; change the
password with `sudo smbpasswd -a <your-username>`.

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
