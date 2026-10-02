# Copying music

There are two ways to get music onto Lauschkiste. Whatever you use, put each album in its own
folder below `library/music` and each audiobook in its own folder below `library/audiobooks` (in
the Lauschkiste home, `lauschctl home` shows where).
The library notices new, changed and removed files by itself and rescans a few seconds after
copying has finished; the refresh button in the web app's library view starts a rescan right away.

## Web app

Open the library in the web app, choose "Local", switch to the folder view and upload files or whole
folders (up to 1 GiB per file) into `music` or `audiobooks`. This needs nothing else and works from
any device, including phones. Only the library is reachable this way.

## Samba (network share)

If you prefer a regular network drive in Windows Explorer or the macOS Finder, enable Samba with
`lauschctl setup samba`. It shares only the library. See [Samba](samba.md).
