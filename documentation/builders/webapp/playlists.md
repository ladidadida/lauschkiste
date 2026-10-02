# Playlists

By default, Lauschkiste represents music based on its metadata like album name, artist or song name. The hierarchy and order of songs is determined by their original definition, e.g. order of songs within an album. If you prefer a specific list of songs to be played, you can use playlists (files ending with `*.m3u`). Radio stations are set up separately, see [Radio](../radio.md).

## Playlists

If you like Lauschkiste to play songs in a pre-defined order, you can use .m3u playlists.

A .m3u playlist is a plain text file that contains a list of file paths or URLs to multimedia files. Each entry in the playlist represents a single song, and they are listed in the order in which they should be played.

### Structure of a .m3u playlist

A .m3u playlist is a simple text document with each song file listed on a separate line. Each entry is optionally preceded by a comment line that starts with a '#' symbol. The actual file paths or URLs of the media files come after the comment.

### Creating a .m3u playlist

1. You can create a .m3u playlist using a plain text editor.
1. Open a new text file
1. [Optional] Start by adding a comment line to provide a description or notes about the playlist.
1. On the following lines, list the file paths or URLs of the media files you want to include in the playlist, one per line. They must refer to true files paths on your Lauschkiste. They can be relative or absolute paths.
1. Save the file with the .m3u extension, e.g. `my_playlist.m3u`.

```text
# Absolute
/home/<username>/lauschkiste/library/music/Simone Sommerland/Die 30 besten Kindergartenlieder/08 - Pitsch, patsch, Pinguin.mp3
/home/<username>/lauschkiste/library/music/Simone Sommerland/Die 30 besten Spiel- Und Bewegungslieder/12 - Das rote Pferd.mp3
# Relative
Bibi und Tina/bibi-tina-jetzt-in-echt-kinofilm-soundtrack/bibi-tina-jetzt-in-echt-kinofilm-soundtrack-7-ordinary-girl.mp3
```

### Using .m3u playlists in Lauschkiste

Lauschkiste Web App handles the playlists in a way that it allows you to browse its content just like other songs. This means, you won't see the m3u playlist itself and instead, the individual items of the playlist. They also become actionable and you can select individual songs from it to play, or play the entire playlist.

> [!NOTE]
> Files ending with `.m3u` are treated as folder playlist. Regular folder processing is suspended and the playlist is built solely from the `.m3u` content. Only the alphabetically first `.m3u` file is processed, others are ignored.

Based on the note above, we suggest to use m3u playlists like this, especially if you like to manage multiple playlists.

1. In the `library/music` directory (or any sub-directory), create a new folder.
1. In this new folder, copy your .m3u playlist. Make sure the links to the respective songs are correct.
1. Open the Web App. Under `Library`, select the `Folder` view and browse to the new folder you created.
1. You should now be able to browse and play the content of the playlist.

#### Example folder structure

```text
└── library/music
    ├── wake-up-songs
    │   └── playlist.m3u
    └── lullabies-sleep-well
        └── playlist.m3u
```

### Assigning a .m3u playlist to a card

In Lauschkiste Web App, .m3u playlists do not show up as individual files. In order to assign a playlist to a card, do the following:

1. [Follow the steps above](#using-m3u-playlists-in-lauschkiste) to add a playlist to your Lauschkiste (make sure you have created individual folders).
1. Open the `Cards` tab in the Web App and click on the `+` button to add a new card.
1. As a Lauschkiste action, select "Play music", then select "Select music".
1. In the `Library` view, select the `Folder` view located in the top right corner.
1. Browse to the folder you created (representing your playlist) and click on it.

You are essentially assigning a folder (just like any other conventional folder) to your card representing the content of your playlist.
