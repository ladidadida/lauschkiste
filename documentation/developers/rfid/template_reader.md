
# Template Reader

> [!NOTE]
> Template for creating and integrating a new RFID Reader.
> For developers only

This template provides the skeleton API for a new Reader. Readers are plugins: a driver
registers at the `rfid.readers` extension point. The bundled drivers live in
`packages/plugins/rfid-readers/src/lauschkiste_plugin_rfid_readers/`; each is exposed as its own plugin
(`rfid_<driver>`) in that package's `pyproject.toml` and `__init__.py`. A driver in its own package
does the same with its own entry point.

Follow the instructions in [template_new_reader.py](../../../packages/plugins/rfid-readers/src/lauschkiste_plugin_rfid_readers/template_new_reader/template_new_reader.py)

Also have a look at the other reader subpackages to see how stuff works
with an example

## File structure

Your new reader is a python subpackage with these three mandatory files

``` bash
lauschkiste_plugin_rfid_readers/awesome_reader/
  +- awesome_reader.py  <-- The actual reader module
  +- description.py     <-- A description module w/o dependencies. Do not change the filename!
  +- README.md         <-- The Readme
```

The module documentation must go into a separate file, called README.md.

## Conventions

- Single reader per directory / subpackage
- reader module directory name and reader module file name must be
    identical
- Obviously awesome_reader will be replaced with something more
    descriptive. The naming scheme for the subpackage is
  - \<type_of_reader\>\_\<io_bus\>\_\<other_specials_like_special_lib\>
  - e.g. generic_usb/generic_usb.py
  - e.g. pn532_spi/pn532_spi.py
  - ...
