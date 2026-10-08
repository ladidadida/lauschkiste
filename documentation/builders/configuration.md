# Lauschkiste Configuration

Lauschkiste configuration is managed by a set of files in the `settings` folder of its home directory
(`$LAUSCHKISTE_HOME`; `lauschctl home` prints it and the configuration file in use. It is `~/lauschkiste` on a
Raspberry Pi and `shared/` in a source checkout).
Some configuration changes can be made through the Web App and take immediate effect.

The majority of configuration options are only available by editing the config files -
*when the service is not running!*
Don't fear (overly), they contain commentaries.

For several aspects, we have [configuration tools](../developers/coreapps.md#configuration-tools) and [detailed guides](./README.md#features).

Even after using the tools, certain aspects can only be changed by directly modifying the configuration files.

API keys and passwords of plugins are not kept in `lauschkiste.yaml` but in `secrets.yaml` next to it
(readable for the box's user only). Set them in the web app or with `lauschctl config set <key> --secret`;
`lauschctl config get` hides them.

## Best practice procedure

```bash
# Make sure Lauschkiste service is stopped
$ systemctl --user stop lauschkiste

# Edit the file(s)
$ nano "$LAUSCHKISTE_HOME/settings/lauschkiste.yaml"

# Start Lauschkiste in console and check the log output (optional)
$ uv run lauschkiste
# and if OK, press Ctrl-C and restart the service

# Restart the service
$ systemctl --user start lauschkiste
```

To try different configurations, you can start Lauschkiste with a custom config file.
This could be useful if you want your Lauschkiste to only allow a lower volume when started
at nighttime, signaling it's time to go to bed. :-)
The path to the custom config file must be either absolute or relative to the repository root
(Lauschkiste daemon's working directory).

```bash
$ uv run lauschkiste --conf /absolute/path/to/custom/config.yaml
```
