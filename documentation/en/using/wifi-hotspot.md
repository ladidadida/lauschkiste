# Away from home: the box opens its own WiFi

On a trip, at grandma's or in the car, there is no WiFi the box knows. With the *hotspot* the box then opens a WiFi of
its own. You connect your phone to it and open the web page as usual.

> [!IMPORTANT]
> The hotspot changes how the box uses the network. If something goes wrong you lose the connection to the box and have
> to put the SD card into a computer to fix it. First make sure the box connects to your home WiFi, and do not switch the
> hotspot on while you can only reach the box by WiFi and have no second way in (screen and keyboard, or a cable).

## Switch it on

```bash
lauschctl setup autohotspot
```

The step needs a Raspberry Pi OS with NetworkManager (the Bookworm and Trixie versions). It asks for a name, a password
and an address for the hotspot. Defaults:

| | Default |
| --- | --- |
| Name (SSID) | `Lauschkiste_<name of the box>` |
| Password | `PlayItLoud!` (change it) |
| Address of the box | `10.0.0.1` |

## Use it

When the box finds no known WiFi (also after a restart), it opens the hotspot after a short time. Connect your phone to
it with the password and open `http://10.0.0.1`. Back home it connects to your WiFi again by itself.

## Add a new WiFi

Connect to the hotspot, log in to the box with SSH (`ssh <user>@10.0.0.1`) and add the WiFi with `sudo raspi-config`
(*System options → Wireless LAN*).

## Switch it off

```bash
sudo systemctl disable --now autohotspot.timer
```

Without it, the box is no longer reachable when no known WiFi is around.

## If it does not work

```bash
sudo systemctl status autohotspot.service
sudo journalctl -u autohotspot.service -n 50
```

If the box does not connect to your home WiFi, it falls back to the hotspot so you still have a way in. Check the
WiFi settings then.
