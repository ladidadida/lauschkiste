# Releasing

All packages are released together under one version (see
[Packaging, Installation and Setup](packaging-and-setup.md#packages-and-releases)). A release is a tag;
the workflow `wheels.yml` builds, tests, creates the GitHub release with the wheels and publishes to
PyPI after a manual approval.

## One-time setup

PyPI needs no token in the repository: the workflow proves its identity to PyPI ("trusted
publishing"). What has to be done once, by the owner of the PyPI account:

1. Create accounts on [pypi.org](https://pypi.org) and [test.pypi.org](https://test.pypi.org) (two
   separate accounts, both with two-factor authentication).
2. On each of them, for every package below, add a **pending publisher** (Account settings →
   Publishing → "Add a new pending publisher"). The package is created by its first upload.

   | Field | Value |
   | --- | --- |
   | PyPI project name | `lauschkiste`, `lauschkiste-core`, `lauschkiste-plugin-board-raspberry-pi`, `lauschkiste-plugin-devices`, `lauschkiste-plugin-mpd`, `lauschkiste-plugin-rfid-readers`, `lauschkiste-plugin-samba` |
   | Owner | `ladidadida` |
   | Repository name | `lauschkiste` |
   | Workflow name | `wheels.yml` |
   | Environment name | `pypi` on pypi.org, `testpypi` on test.pypi.org |

3. In the GitHub repository (Settings → Environments) create the environments `testpypi` and `pypi`.
   Give `pypi` **required reviewers** (yourself): a PyPI upload cannot be undone, so the workflow waits
   for an approval before it publishes.

## Test on TestPyPI

Every upload needs a version that was not used before, so test with development versions:

```bash
ci/set_version.py 0.1.0a4.dev1
git commit -am "Version 0.1.0a4.dev1" && git push
```

Run the workflow "Wheels and install" by hand (Actions → Run workflow, tick "Publish this ref to
TestPyPI"). When it is green, install from there on a fresh machine:

```bash
curl -fsSL https://raw.githubusercontent.com/ladidadida/lauschkiste/main/install.sh \
  | bash -s -- --from testpypi --version 0.1.0a4.dev1
```

TestPyPI only has the Lauschkiste packages; the installer takes everything else from PyPI.

## Release

1. Set the version and commit it: `ci/set_version.py 0.1.0-alpha.4`.
2. Tag it and push the tag: `git tag v0.1.0-alpha.4 && git push origin v0.1.0-alpha.4`. The workflow checks
   that the tag matches the version.
3. The workflow builds, runs the install tests (from wheels, from a package index, from the source), creates
   the GitHub release (a pre-release while the tag has a suffix) and then waits for your approval of the
   `pypi` environment. After the approval the packages are on PyPI.
4. Check: `uv tool install lauschkiste` on a machine, `lauschctl plugin list`.

While there are only pre-releases, `pip install lauschkiste` needs `--pre` (uv and the installer do not).

## What is checked before publishing

- `uvx twine check dist/*`: the descriptions render on PyPI.
- `test/test_packaging.py`: names, one version, exact pins, README and LICENSE in every package.
- Installation in fresh Debian containers from the wheels, from a package index built from the release files
  and from a checkout.
