# Updating and removing

## Update

Log in to the box with SSH and run:

```bash
lauschctl update --check     # is there a newer version?
lauschctl update             # install it, apply the setup again, restart Lauschkiste
```

`lauschctl update` follows the way Lauschkiste was installed: from PyPI it upgrades from PyPI, from release wheels
(`--from github`) it takes the newest release, and a source checkout (`--from source`) pulls its branch.
`--version <version>` picks a specific version. Plugins you installed yourself stay.

Afterwards the setup runs again with your earlier answers (for example to update the service definition), and a running
Lauschkiste is restarted. Music, settings and cards are in the Lauschkiste home and are not touched.

> [!NOTE]
> Boxes with a version before 0.1.0a7 cannot update with `lauschctl update`: the plugins moved into two packages
> (`lauschkiste-plugins`, `lauschkiste-plugins-raspberry-pi`), and the old program does not know that. Run the
> installer once instead (`curl -fsSL https://raw.githubusercontent.com/ladidadida/lauschkiste/main/install.sh | bash`),
> then `lauschctl setup`. Settings, cards and library stay. From 0.1.0a7 on `lauschctl update` works as described.
>
> There is no way to carry over settings or cards from Phoniebox 2.x; install Lauschkiste on a fresh SD card.

## Remove

```bash
lauschctl uninstall --check   # what would be removed, and what stays
lauschctl uninstall           # remove it; asks before it deletes your data
```

It removes what Lauschkiste itself created: its services, the forwarding of port 80, the login message, the kiosk and
Samba entries, the lines the installer added to your shell profile, and finally Lauschkiste with its commands. Your data
(music, settings, cards) stays unless you answer *yes* or pass `--remove-data`. A source checkout is not deleted.

What belongs to the system stays, and the command lists it with how to undo it by hand: system packages (`apt remove`),
boot settings (sound card lines, quiet boot), network settings (hotspot, console login) and the Samba user.
