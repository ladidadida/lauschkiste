# Known Issues

## Legacy ZeroMQ leftovers

This fork removed ZeroMQ entirely (RPC, pub/sub, and the C CLI client all moved to FastAPI/HTTP --
see `documentation/developers/roadmap-core-architecture.md`). An installation upgraded from before
that change may still have `libzmq5`/`python3-zmq` (apt) installed, or -- from even older releases
-- the project's custom libzmq archive under `/usr/local`. None of it is needed by Lauschkiste
anymore. First check what's actually installed:

```bash
ldconfig -p | grep libzmq
dpkg -l libzmq5 python3-zmq 2>/dev/null
```

If a custom `/usr/local` archive is present (only if it's known to have been installed by
Lauschkiste -- do not remove unrelated files from `/usr/local`):

```bash
sudo rm -f /usr/local/lib/libzmq.so*
sudo rm -f /usr/local/lib/pkgconfig/libzmq.pc
sudo rm -f /usr/local/include/zmq.h /usr/local/include/zmq_utils.h
sudo rm -rf /usr/local/lib/cmake/ZeroMQ
sudo ldconfig
```

The apt packages can be removed the normal way (`sudo apt-get remove libzmq5 python3-zmq`) once
nothing else on the system needs them.

## Configuration

Relative paths in `lauschkiste.yaml` (and all other config files) are resolved against the
Lauschkiste home (`lauschctl home`); absolute paths and paths starting with `~/` are used as given.
