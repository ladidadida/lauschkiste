# Python Development Notes

All Python code runs in a virtual environment. In a source checkout, [uv](https://docs.astral.sh/uv/) creates
it (`uv sync --group dev`) and runs commands in it:

```bash
uv run lauschkiste        # the server
uv run lauschctl --help   # the management tool
uv run pytest             # the tests
```

To work in the environment directly, activate it (`source .venv/bin/activate`) and leave it again with
`deactivate`. A box installed with `install.sh --from github|pypi` keeps Lauschkiste in its own environment (a pip venv in
`~/.local/share/lauschkiste-venv`, or uv's tool environment when uv was used); `lauschkiste` and `lauschctl` are on the
`PATH` there and `lauschctl plugin install` adds packages to it. `install.sh --from source` also installs the
development tools including `bam`.
