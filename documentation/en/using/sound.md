# Sound and Bluetooth

The box plays through the sound output of the Raspberry Pi: the headphone jack, a USB speaker, HDMI, a sound card that
sits on the header ([sound cards](../hardware/sound-cards.md)), or Bluetooth. Sound goes through PipeWire, which
current Raspberry Pi OS brings along.

Lauschkiste knows **two outputs**: the *primary* one, which must be there after every start (your speaker or sound card),
and an optional *secondary* one for Bluetooth headphones or a Bluetooth speaker. In the web page you switch between them.

## No sound?

Check on the box (log in with SSH, see [Install](../get-started/install.md#2-log-in-to-the-box)):

```bash
wpctl status                                       # lists the outputs ("Sinks"), the starred one is the default
wpctl set-default <id>                             # make another one the default
alsamixer                                          # volume of the sound card (leave with Esc)
pw-play /usr/share/sounds/alsa/Front_Center.wav    # play a test sound
```

If the test sound works but Lauschkiste is silent, look at Settings → Playback and audio and at the volume limit. If
even the test sound is silent, the problem is the sound card, not Lauschkiste.

## Choosing the outputs

```bash
lauschctl setup audio
```

lists the outputs of the box and asks which one is primary and which one secondary. Outputs of sound cards are named
after the card (for example "HiFiBerry DAC+"). Without this step the box uses the system's default output.

## Bluetooth headphones or speaker

Pair once, then register the device as the secondary output.

```bash
bluetoothctl
```

Put the headphones into pairing mode, then in `bluetoothctl`:

```text
scan on          wait until your device shows up, note its address (C4:FB:20:63:C0:FE)
scan off
pair C4:FB:20:63:C0:FE
trust C4:FB:20:63:C0:FE
connect C4:FB:20:63:C0:FE
exit
```

If `bluetoothctl` complains about permissions, start it with `sudo`. After a few seconds `wpctl status` should list the
device as an output (`bluez_output...`); test it with `pw-play`. If not, switch the headphones off and on. Then run
`lauschctl setup audio` again and choose the headphones as the secondary output.

Bluetooth is on by default; do not answer *yes* to "also switch Bluetooth off" in `lauschctl setup`.

## Buttons on Bluetooth headphones

The play, next, previous and volume buttons of headphones appear as input devices. To let the box react to them, set
`input.media_keys: true` in the settings (off by default so a keyboard on a desktop computer does not take over). The
buttons run the matching actions (pause, next, volume). Other keys and USB buttons are described in
[Buttons and knobs](../hardware/buttons.md).

To change between the speaker and the headphones from a card or a button, use the action `volume.toggle_output`.

## Volume

- The slider in the player sets the volume.
- `volume.soft_max_volume` (default 70) is the highest volume that can be set, a protection for ears. Change it in the
  web page under Settings → Playback and audio.
- `volume.startup_volume` (default 40) is the volume after a start.
