# Library

## Layout

The library is organised by content:

| Tab | Content |
| --- | --- |
| Continue | audiobooks in progress and podcasts with new episodes |
| Music | all albums; under "Folders" the files in `library/music` |
| Audiobooks | all audiobooks with progress; under "Folders" the files in `library/audiobooks` |
| Radio | internet radio stations |
| Podcasts | subscribed podcasts and their episodes |

## Uploading

Under Music → Folders or Audiobooks → Folders, tap "Upload" and choose files or whole folders (up to 1 GiB per file). On a computer you can also drag files into the list.

- **Music:** one folder per album. Title, artist and cover come from the files or from a picture in the folder (`cover.jpg`).
- **Audiobooks:** one folder per audiobook. The files are the chapters and play in file name order (`2` before `10`).

New files show up after a few seconds by themselves; the refresh button rescans right away.

## Network drive (Samba) {#samba}

For large collections the library can be opened as a network drive in Windows Explorer or the macOS Finder. Samba is installed once on the box ([Commands on the box](/help/lauschctl?section=samba)); then you switch the share on under Settings → Library.

### User and password

- **User name** is the user Lauschkiste runs as on the box, the one you also log in with over SSH (e.g. `pi`). There is no other user; the settings page shows the name.
- **Password** is a Samba password of its own, separate from the login password of the box. Set or change it under Settings → Library → "New Samba password" (at least 8 characters). The new password replaces the old one right away.

### Connecting

| Computer | How |
| --- | --- |
| Windows | in Explorer's address bar enter `\\<name-of-the-box>\lauschkiste` |
| macOS | Finder → Go → Connect to Server → `smb://<name-of-the-box>/lauschkiste` |
| Linux | open `smb://<name-of-the-box>/lauschkiste` in the file manager |

The first time, the computer asks for user name and password; "remember password" saves typing them again. The IP address works instead of the name too (Settings → Status).

## Radio

Under Radio → "Add station" enter a name and the stream address. `.m3u` and `.pls` links from station websites work too.

## Podcasts

Under Podcasts → "Subscribe to podcast" enter the address of the RSS feed (not of the website). Episodes are streamed, so the box needs internet. "Play newest unheard episode" works well on a card.
