# Releasing

All packages are released together under one version (see
[Packaging, Installation and Setup](packaging-and-setup.md#packages-and-releases)). A release is a tag;
the workflow `wheels.yml` builds, tests, creates the GitHub release with the wheels and publishes to
PyPI after a manual approval (one job per package).

## Before the first release

- [ ] Clarified with the Phoniebox project: that Lauschkiste is named as its origin, and the origin of the
  start and shutdown sounds.
- [x] Searched for conflicts with the name "Lauschkiste" (trademark registers of the DPMA and EUIPO) and for
  similar logos (October 2026: no problems expected).
- [x] Private vulnerability reporting is switched on (repository Settings → Code security): the Code of
  Conduct and `SECURITY.md` send reports there.
- [x] Repository description, topics and social preview image are set.
- [ ] The accounts, pending publishers and environments below exist.
- [ ] A test upload to TestPyPI and a fresh installation from it on a box worked.

## One-time setup

PyPI needs no token in the repository: the workflow proves its identity to PyPI ("trusted
publishing"). What has to be done once, by the owner of the PyPI account:

1. Create accounts on [pypi.org](https://pypi.org) and [test.pypi.org](https://test.pypi.org) (two
   separate accounts, both with two-factor authentication).
2. On each of them, for every package below, add a **pending publisher** (Account settings →
   Publishing → "Add a new pending publisher", tab GitHub). The package is created by its first upload.
   The same four values everywhere:

   | Field | Value |
   | --- | --- |
   | Owner | `ladidadida` |
   | Repository name | `lauschkiste` |
   | Workflow name | `wheels.yml` |

   PyPI accepts one configuration as pending for **one** new project only, so every package has its own
   environment name: `testpypi-<project>` on test.pypi.org and `pypi-<project>` on pypi.org.

   | PyPI project name | Environment name on test.pypi.org | on pypi.org |
   | --- | --- | --- |
   | `lauschkiste` | `testpypi-lauschkiste` | `pypi-lauschkiste` |
   | `lauschkiste-core` | `testpypi-lauschkiste-core` | `pypi-lauschkiste-core` |
   | `lauschkiste-plugin-board-raspberry-pi` | `testpypi-lauschkiste-plugin-board-raspberry-pi` | `pypi-lauschkiste-plugin-board-raspberry-pi` |
   | `lauschkiste-plugin-devices` | `testpypi-lauschkiste-plugin-devices` | `pypi-lauschkiste-plugin-devices` |
   | `lauschkiste-plugin-mpd` | `testpypi-lauschkiste-plugin-mpd` | `pypi-lauschkiste-plugin-mpd` |
   | `lauschkiste-plugin-rfid-readers` | `testpypi-lauschkiste-plugin-rfid-readers` | `pypi-lauschkiste-plugin-rfid-readers` |
   | `lauschkiste-plugin-samba` | `testpypi-lauschkiste-plugin-samba` | `pypi-lauschkiste-plugin-samba` |

   PyPI allows **three pending publishers at a time** (an entry no longer counts once its first upload
   has created the project). So register three, upload, register the next three and upload again; see
   "Packages in rounds" below.

3. In the GitHub repository (Settings → Environments) create the environment `pypi` and give it **required
   reviewers** (yourself): it is the gate before the upload to PyPI, which cannot be undone. The other
   environments (`testpypi-...`, `pypi-...`) are created by GitHub when the workflow first uses them; they
   need no settings.

## Packages in rounds

The workflow has one job per package. A job whose package has no trusted publisher yet fails with
"invalid-publisher", the others succeed. After each upload that created projects:

1. Register the next (up to three) pending publishers of the packages that failed.
2. In the workflow run on GitHub choose **Re-run failed jobs**: only those uploads run again.

Repeat until all seven jobs are green (three rounds: 3 + 3 + 1). This is needed once per registry (TestPyPI,
PyPI); later uploads need no pending publishers any more.

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
5. After the **first** release on PyPI: make `pypi` the default of `install.sh` (`FROM=pypi`) and in
   [Installation](../builders/installation.md) and [Update](../builders/update.md) (the table of `--from`, the
   curl line without `--from`), and say so in the README.

While there are only pre-releases, `pip install lauschkiste` needs `--pre` (uv and the installer do not).

## What is checked before publishing

- `uvx twine check dist/*`: the descriptions render on PyPI.
- `test/test_packaging.py`: names, one version, exact pins, README and LICENSE in every package.
- Installation in fresh Debian containers from the wheels, from a package index built from the release files
  and from a checkout.
