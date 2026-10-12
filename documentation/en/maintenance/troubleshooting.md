# When something does not work

Go from top to bottom. Most problems are solved by one of the first steps.

## 1. What does the setup say?

```bash
lauschctl setup --check
```

lists every setup step as *ok* or *to do*. Run `lauschctl setup <step>` for a step that is *to do*, or `lauschctl setup`
for all of them. Steps only change what is missing; running them again does no harm.

## 2. Is Lauschkiste running?

```bash
systemctl --user status lauschkiste
```

If it is not running, start it with `systemctl --user start lauschkiste`. If it stops again, read the log (below).

## 3. Does the sound work?

See [No sound?](../using/sound.md#no-sound).

## 4. The web page does not open

- Is the box on the same WiFi as your device? Try the address instead of the name: look it up in your router, or log in
  with SSH and run `hostname -I`.
- Without port 80 the address needs `:5556`: `http://<name>:5556`.
- After a restart the box needs a minute.
- A card or the action `system.say_my_ip` makes the box read out its IP address.

## 5. Read the log

```bash
journalctl --user -b -u lauschkiste          # everything since the last start
```

Lauschkiste also writes files in the `logs` folder of its home (`lauschctl home`):

| File | Content |
| --- | --- |
| `app.log` | complete debug messages of the current run |
| `errors.log` | only warnings and errors |

The previous run is kept as `app.log.1`. The same logs can be read in a browser at `http://<name>/logs`. Always check
the date of the file: you may be looking at an old one.

To watch the messages live, stop the service and start Lauschkiste in the console:

```bash
systemctl --user stop lauschkiste
lauschkiste -vv
```

Stop it with Ctrl-C and start the service again afterwards.

## 6. Reader and cards

- The reader is found by `lauschctl setup rfid`; connect USB readers *before* you run it.
- A card the box does not know shows **Register** in the player. If nothing shows, the reader is not working: run
  `lauschkiste -vv` and hold a card on it.
- Cards of the wrong frequency are not read. See [RFID readers](../hardware/readers.md).

## 7. Still stuck?

Ask in the project's [issues](https://github.com/ladidadida/lauschkiste/issues) and include the output of
`lauschctl setup --check`, `lauschctl plugin list` and the last lines of `errors.log`.
