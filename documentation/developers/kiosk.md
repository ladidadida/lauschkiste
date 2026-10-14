# The kiosk: what the screen on the box shows

A box with a screen should show something a child can use without changing settings. The normal web app offers
everything, so the screen can show a **kiosk app** instead: a reduced view served by the core under `/kiosk/`. The
normal web app stays as it is: the administration and the fallback, plain on purpose, it only has to work.

## Parts

| Part | Content |
| --- | --- |
| `lauschctl setup kiosk` | installs the graphics system and Chromium, sets up the autologin and opens `/kiosk/` after the start (a start page waits for the service first) |
| Core module `kiosk` (`box/kiosk/module.py`) | settings `enabled` (off by default) and `app`; serves the chosen app at `/kiosk/`, or forwards to the normal web app (`/?kiosk`) when the kiosk is off; the extension point `kiosk.apps`; the event `kiosk.state` |
| Core module `kiosk_standard` (`box/kiosk/standard.py`) | the first kiosk app, registered at `kiosk.apps` like any other; its settings; the themes |
| Web app, `kiosk.html` and `src/kiosk/` | the standard app: a second entry of the same Vite build, sharing components with the normal web app (cover, controls, seek bar, volume) |
| *Settings → Screen* | the keyboard, switching off (`display`), the kiosk on or off, the choice of the app and below it the settings of the chosen app |

Everything that changes the operating system stays with `lauschctl` (the browser, the autologin); the web app only
chooses what the browser shows. The browser always opens `/kiosk/`, so nothing on the box changes when the kiosk is
switched on or off or another app is chosen: the screen follows by itself (the event `kiosk.state`; the normal web app
on the box's screen jumps to `/kiosk/` when the kiosk is switched on, a kiosk app goes back to `/?kiosk` when it is
switched off).

## The standard kiosk app

- **Pages:** the player (cover, title, seek bar, controls, volume) and the library as big tiles: "Continue", music,
  audiobooks, radio, podcasts (a podcast opens its episodes). A tap plays and returns to the player. No settings, no
  card management. After two minutes without a touch it returns to its start page.
- **Settings** (module `kiosk_standard`, shown below the kiosk settings): `theme`, `text_size`, `start_page`, one
  switch per page (`show_continue`, `show_music`, `show_audiobooks`, `show_radio`, `show_podcasts`) and `show_volume`.
  The module publishes them as the event `kiosk_standard.settings`, so a change shows on the screen at once.
- **Themes:** a theme is a CSS file with the custom properties `--kiosk-mode` (`dark` or `light`),
  `--kiosk-background`, `--kiosk-surface`, `--kiosk-text`, `--kiosk-muted`, `--kiosk-accent`, `--kiosk-accent-text`,
  `--kiosk-radius` and `--kiosk-font` on `:root`; colours as `#rrggbb`. The app loads the file, reads the properties and
  builds its MUI theme from them. Built-in ones are in `resources/kiosk-themes/`; further ones are files in
  `kiosk-themes/` in the data directory (a file there replaces a built-in theme of the same name). The theme is a
  setting of the app, not a plugin of its own.
- **No new rights:** the app uses the same API and event stream as the normal web app. It is a simplification, not a
  lock: anyone who can open the normal web app in a browser can still change everything.

## Writing another kiosk app

A kiosk app is a module (usually a plugin) that registers at the extension point `kiosk.apps`; the key is the module's
name, which is also where its settings live:

```python
from pathlib import Path
from lauschkiste.contract import Plugin


class MyKioskApp(Plugin):
    """A kiosk with pictures only."""

    name = 'my_kiosk'
    requires = ('kiosk',)
    title = 'Pictures'       # shown in the choice
    entry = 'index.html'     # the page served at /kiosk/ (default)
    settings = MySettings    # optional: shown below the kiosk settings when the app is chosen

    def start(self, ctx):
        ctx.modules.kiosk.apps.register(self.name, self)

    def directory(self) -> Path:
        return Path(__file__).parent / 'web'   # the folder with the built web files
```

- The core serves the files of that folder below `/kiosk/`: a build with relative paths (Vite's `base: './'`) works as it
  is. Files below `assets/` are cached for good, so give them content hashes.
- The app talks to the same `/api/v1/*` routes and `/api/v1/events` WebSocket as the normal web app. It follows the
  kiosk by the event `kiosk.state` (`enabled`, `app`, `apps`): leave when `enabled` is false, reload when `app` is
  another one.
- Publish the app's settings as an event of its own if the page should follow changes at once (the standard app does).
- A plugin that is not enabled or fails to start is not offered; if the chosen app is gone the standard app takes over.

## Input on a touch screen

The settings pages of the normal web app are also used on the touch screen. Numbers with fixed limits are sliders
(steps up to 300; a `step` entry in the field's JSON schema sets the step), and choices are selection lists and switches.

- **On-screen keyboard** (done): a component of the normal web app, `src/components/OnScreenKeyboard`, built on
  `react-simple-keyboard`. It opens when a text field gets the focus, moves the page and dialogs so the field stays
  visible, and has letters (German and English layout), symbols, shift, backspace, enter and hide. It appears only on the
  screen on the box: the start page opens the web app with `?kiosk`, which the browser remembers, since a browser
  cannot tell a touch screen with a keyboard from one without. The switch is the web app setting `on_screen_keyboard`
  (*Settings → Screen*), for boxes with a physical keyboard. Open: a numeric layout for number fields and a show/hide
  switch for passwords.
- **Wide scrollbars** on touch devices (`pointer: coarse`).
- **Less typing:** wherever the backend can offer a list (audio devices, library folders, known actions), the field
  becomes a selection list; big numbers get a stepper with large buttons instead of the keyboard.

## Open points

- **The device.** Chromium in kiosk mode is the heavy part: the normal web app is about 1.2 MB of JavaScript (not
  compressed). A Pi Zero W with 427 MB RAM is probably too small for a Chromium kiosk; a Pi 3 or Zero 2 and better should be
  fine. Not yet measured on a real screen.
- **Idle behaviour:** what the screen shows when nothing plays (a clock, the last cover, dark)?
- **Queue:** should a child see the queue, or only the current title? Only the current title for now.
- **A way out:** from the kiosk app there is none, by design (Chromium's `--kiosk` already prevents leaving it);
  switch the kiosk off from a phone in *Settings → Screen*.
