# Bluetooth audio buttons

Headsets and Bluetooth speakers expose their play/pause/next/previous/volume buttons as input
devices. Let Lauschkiste react to them with the media keys of the core `input` module:

```yaml
input:
  media_keys: true
```

This maps `KEY_PLAYPAUSE`, `KEY_PLAYCD`, `KEY_PAUSECD`, `KEY_STOPCD`, `KEY_NEXTSONG`,
`KEY_PREVIOUSSONG`, `KEY_VOLUMEUP`, `KEY_VOLUMEDOWN` and `KEY_MUTE` of any device that has such
keys to the matching [actions](actions.md). It is off by default so Lauschkiste running on a desktop
doesn't take over the keyboard's media keys. Devices connecting later are picked up automatically.

Switching the audio output to the headset is done with `volume.toggle_output` or in the web app's
audio settings (see the `volume.outputs` configuration).
