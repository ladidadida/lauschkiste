# Copying music

There are three ways to get music onto Lauschkiste. Whatever you use, put each album or audiobook
in its own folder below `audiofolders` (in the Lauschkiste home, `lauschctl home` shows where).
The library notices new, changed and removed files by itself and rescans a few seconds after
copying has finished; the refresh button in the web app's library view starts a rescan right away.

## Web app

Open the library in the web app, switch to the folder view and upload files or whole folders. This
needs nothing else and works from any device, including phones. For large collections the other
two ways are more comfortable.

## SFTP

SFTP works out of the box on a Raspberry Pi with SSH enabled (the default when you set up the SD
card with the Raspberry Pi Imager). Log in with the same user and password (or SSH key) you use for
SSH.

| On | Use |
| --- | --- |
| Windows | [WinSCP](https://winscp.net/) or [FileZilla](https://filezilla-project.org/): protocol SFTP, host `<your-pi>`, port 22 |
| macOS | FileZilla or [Cyberduck](https://cyberduck.io/); or in a terminal `scp -r "My Album" <user>@<your-pi>:lauschkiste/audiofolders/` |
| Linux | the file manager: `sftp://<user>@<your-pi>/home/<user>/lauschkiste/audiofolders` |

On a Raspberry Pi the music folder is `~/lauschkiste/audiofolders` (or `~/jukebox/audiofolders` on
installations from before the renaming).

## Samba (network share)

If you prefer a regular network drive in Windows Explorer or the macOS Finder, enable Samba with
`lauschctl setup samba`. It shares only the music folder. See [Samba](samba.md).
