# A screen on the box

A small screen (a Raspberry Pi display, an HDMI screen) can show the web page of the player on the box, so it needs no
phone. It is the same web page, full screen, or, switched on in the settings, a reduced view for children (see
[The kiosk](#the-kiosk-a-reduced-view-for-children)).

## Switch it on

```bash
lauschctl setup kiosk
```

(or answer *yes* to "Show the web app full-screen on an attached display" in `lauschctl setup`). The step installs a
minimal graphics system (X server, the openbox window manager and the Chromium browser, not a full desktop), logs in on
the first console by itself and starts the browser in full screen after the start. Restart the box. A Raspberry Pi 3
or better is advised; a Zero is slow with a browser.

## Typing on the screen

Tap a text field (for example the search for radio stations) and a keyboard appears at the bottom of the screen. The
key with the arrow hides it again. It appears only on the screen on the box, not on your phone or computer. If you
attach a physical keyboard, switch it off in *Settings → Screen → On-screen keyboard*.

A box set up with an older version needs `lauschctl setup kiosk` once, so that the screen knows it is the one on the box.

## The kiosk: a reduced view for children

The normal web page shows everything, including the settings. The kiosk is a reduced view for the screen on the box:
the player and the library as big tiles (continue, music, audiobooks, radio, podcasts), with no settings and no card
management. Switch it on in the web app under *Settings → Screen* (*Show the kiosk app on the screen*); the screen
changes by itself, no restart is needed. Below it you find the settings of the kiosk app: the look (*Night*, *Day*,
*Meadow*, *Candy*), the text size, which pages are offered and whether the volume control is shown. After two minutes
without a touch the screen returns to its start page.

It is a simplification, not a lock: whoever opens the web page on a phone or computer can still change everything. To get
the normal web page back on the screen, switch the kiosk off in the settings, from a phone. Your own looks are CSS
files in the folder `kiosk-themes` of the data directory; see [Kiosk](../../developers/kiosk.md#the-standard-kiosk-app).

## Switch the screen off when nobody uses it

After 5 minutes without a touch the screen goes dark. A touch switches it on again, and that touch only wakes the
screen: it does not press anything in the web app. The music keeps playing; only the screen sleeps. This saves power and
keeps the screen from burning in on a box that runs all day.

Change the time in the web app under Settings → Screen → *Switch the screen off after (minutes)*; `0` keeps the screen
on. It takes effect at once. This works for screens whose backlight Lauschkiste may control, like the official Raspberry
Pi touch display. Most HDMI monitors have no such backlight and stay on.

A card put on the reader, a button or a key (see [Buttons](buttons.md)) wakes the screen too. If you do not want the
screen to go dark while music plays, switch on *Keep the screen on while music plays* in the same place.

The actions `display.sleep` and `display.wake` switch the screen off and on, for example from a card or a button.

## If the screen stays black

- Check that the web page itself works from another device.
- A screen that is switched off by the timer above looks black too: touch it.
- The browser is called `chromium-browser` on Raspberry Pi OS up to Bookworm and `chromium` from Trixie on. The step
  chooses the right one; run it again after an update of the system.
- Run `lauschctl setup --check`: it lists what is wrong with the kiosk.
- A touch screen works like a mouse. If the touch is mirrored or turned, that is a setting of the display driver, not
  of Lauschkiste.

## Switch it off

`lauschctl uninstall` removes the kiosk entries. To only turn it off, remove the line that starts Chromium from
`/etc/xdg/openbox/autostart`, and the console login in
`/etc/systemd/system/getty@tty1.service.d/autologin.conf`.
