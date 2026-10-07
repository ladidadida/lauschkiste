# Contributing

Thank you for helping! Bug reports, ideas, documentation and code are all welcome. Please follow the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Report a problem or propose something

- Bugs and ideas: open an [issue](https://github.com/ladidadida/lauschkiste/issues) and use the template.
- Larger features: open an issue first and describe what you plan, so that nobody builds the same thing twice
  and the design fits (see [the developer documentation](documentation/developers/README.md)).
- Security problems: see [SECURITY.md](SECURITY.md).

## Development

[AGENTS.md](AGENTS.md) describes the repository, the tools and the common commands. In short:

```bash
uv sync --group dev                  # Python environment
uv run pytest                        # tests
uv run ruff check .                  # lint
cd packages/webapp && npm ci && npm run build    # web app; also: npm run lint, npm test, npm run test:e2e
uv run lauschkiste                   # run it from the checkout
```

## Conventions

- Python: [PEP 8](https://www.python.org/dev/peps/pep-0008/), line length 127; names in English.
- Files and folders are lower case; words are separated with an underscore in Python packages.
- New behaviour comes with tests; changed interfaces of core modules and plugins need their snapshots
  updated (`uv run python -m lauschkiste.contract.snapshots --update`).
- Texts in the web app are translated (German and English, `packages/webapp/public/locales`); help pages
  are in `packages/webapp/public/help/{de,en}`.
- Documentation is in English. Describe a larger change in `documentation/developers` before or with the code.
- Commit messages: a short summary line in the imperative, then what and why.

## Pull requests

Keep a pull request to one topic and make sure the checks of the repository pass (Python tests and lint, web
app tests, Markdown lint, installation tests). A maintainer reviews it; small fixes are quick, larger changes
may need a discussion first.

By contributing you agree that your work is published under the [MIT license](LICENSE).
