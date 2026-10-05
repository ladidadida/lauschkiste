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

## Network drive (Samba)

For large collections the library can be opened as a network drive in Windows Explorer or the macOS Finder. Samba is installed once on the box ([Commands on the box](/help/lauschctl?section=samba)); then you switch the share and its password under Settings → Library.

## Radio

Under Radio → "Add station" enter a name and the stream address. `.m3u` and `.pls` links from station websites work too.

## Podcasts

Under Podcasts → "Subscribe to podcast" enter the address of the RSS feed (not of the website). Episodes are streamed, so the box needs internet. "Play newest unheard episode" works well on a card.
