# Audiobooks

Audiobooks are folders in `library/audiobooks`, one folder per book ([Music and the library](music.md)). The files are
the chapters and play in the order of their names (`2.mp3` before `10.mp3`).

A book **continues where it stopped**, a few seconds earlier so the listener finds back in. The position is saved while
playing, when pausing and when the box shuts down. When the last chapter has played to the end, the book counts as
finished; it stays loaded, back at its beginning, so play starts it again. Chapters always play in order, whatever
shuffle and repeat say.

After a restart the box loads what played last (a book, but also music, a playlist, a podcast or a station), paused
where it stopped: play continues.

## Editing a book

Title, author and cover come from the tags of the files (the title from the album tag, or the folder name when there is
none). The menu of a book in the web app has **Edit**:

- **Title** and **author**: an empty field goes back to the value from the files.
- **Cover**: *Choose picture* uploads an image (JPEG, PNG, WebP or GIF, up to 10 MB) that replaces the covers of the
  files; *Use the cover from the files* goes back.
- **Chapters**: change their order with the arrows and give them names. The names show in the player while the chapter
  plays.

The changes are saved in `book.json` (and the picture as `book-cover.*`) in the book's folder. The audio files and the
folder name stay as they are, so the position and the cards keep working. Books of an Audiobookshelf server keep what
the server says.

## On a card

Play the book and tap the card button in the player, as in [Your first card](../get-started/first-card.md), or
choose *Play audiobook* when registering a card in the card list. Placing the card for the book that is already playing changes nothing; a
paused book continues. With a reader that notices the card staying on the box, taking the card off pauses and putting it
back continues ([Cards](cards.md#cards-that-stay-on-the-box)).

Further actions for cards: `audiobooks.restart` (from the beginning) and `audiobooks.set_finished` (mark as finished or
not).

How far back a book goes when it continues is `audiobooks.rewind_sec` (default 10 seconds).

## Audiobookshelf

The plugin *Audiobookshelf* shows the books of an [Audiobookshelf](https://www.audiobookshelf.org) server next to the
local ones and plays them from the server. The position is kept on the server: a book started in the Audiobookshelf app
continues on the box and the other way round.

1. In Audiobookshelf create an API key (Settings → API Keys) for the user the box should use.
2. In the web page open Settings → Plugins, switch on *Audiobookshelf* and enter the address of the server and the key.
   The key is kept in a file only the box's user can read and is never shown again.
3. The books appear under Audiobooks. On a card they work like local books.

A book that is not downloaded needs the server to play.

### Download books

The menu of an Audiobookshelf book has **Download to the box**. The files go to `cache/audiobookshelf` in the
Lauschkiste home. A downloaded book plays from the box even when the server is there. While something plays, the
download is slowed down so the sound never stutters. Settings → Library → Cache sets the space for all downloads
(8 GB by default). When it is full and *remove old* is on, the oldest finished downloads are removed; books in progress
never are. If the server changed a book after the download, the list says so, and *Download again* fetches the new
version.

### When the server is away

The box keeps playing: the book list is kept, downloaded books come first, and the position is saved on the box and sent
to the server as soon as it is back. If a book was also listened to elsewhere meanwhile, the furthest position wins and a
finished book stays finished.

### Moving to the box from other apps

Podcasts from other apps move over with an OPML file, see [Podcasts](podcasts.md#from-and-to-other-apps).
