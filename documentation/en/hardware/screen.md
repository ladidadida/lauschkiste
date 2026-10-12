# A screen on the box

A small screen (a Raspberry Pi display, an HDMI screen) can show the web page of the player on the box, so it needs no
phone. It is the same web page, full screen. A reduced view for children is planned (see the
[plan](../../developers/kiosk.md)); for now the screen shows everything including the settings.

## Switch it on

```bash
lauschctl setup kiosk
```

(or answer *yes* to "Show the web app full-screen on an attached display" in `lauschctl setup`). The step installs a
minimal graphics system (X server, the openbox window manager and the Chromium browser, not a full desktop), logs in on
the first console by itself and starts the browser in full screen after the start. Restart the box. A Raspberry Pi 3
or better is advised; a Zero is slow with a browser.

## Switch the screen off when nobody uses it

After 5 minutes without a touch the screen goes dark. A touch switches it on again, and that touch only wakes the
screen: it does not press anything in the web app. The music keeps playing; only the screen sleeps. This saves power and
keeps the screen from burning in on a box that runs all day.

Change the time in the web app under Settings → System → *Switch the screen off after (minutes)*; `0` keeps the screen
on. It takes effect at once. This works for screens whose backlight Lauschkiste may control, like the official Raspberry
Pi touch display. Most HDMI monitors have no such backlight and stay on.

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
