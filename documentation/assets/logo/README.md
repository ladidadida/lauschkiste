# Logo

The Lauschkiste bear, in seven colors, with and without the name, on a transparent or a white background.

```text
transparent/lauschkiste-logo[-text]-<color>.svg
white/lauschkiste-logo[-text]-<color>-white.svg
```

- Colors: `berry` (the default), `tomato`, `ochre`, `sun-yellow`, `forest`, `teal`, `night-blue`.
- `-text` is the logo with the name (the letters are paths, no font is needed); without it, only the bear.
- Default: `white/lauschkiste-logo-text-berry-white.svg` where the name fits (README, documents),
  `white/lauschkiste-logo-berry-white.svg` where only the bear fits (icons).

The web app has its own copies in `packages/webapp/public`: `logo.svg` is the default bear, `logo192.png` and
`favicon.ico` are made from it on a square white tile (the app icon of phones and the browser tab).

## Use

The MIT license of the repository covers the code. For the logo this note applies.

The logo may be used to refer to Lauschkiste: links, articles, talks, "works with Lauschkiste" notes, and in forks
that clearly say that they are forks. Please do not alter it, and do not use it (or a confusingly similar one) as
the logo of another project, of a modified version of Lauschkiste or of a product, or in a way that suggests the
project endorses it. Modified versions and other projects should use their own name and logo.

## Social preview

`documentation/assets/social-preview.png` (1280×640, under 1 MB) is the image shown when the repository is linked;
it is set in the repository settings (Settings → General → Social preview). It is made from the default logo
and a line of text (`social-preview.svg`, set in Quicksand):

```bash
inkscape -w 1280 -h 640 documentation/assets/social-preview.svg -o documentation/assets/social-preview.png
```
