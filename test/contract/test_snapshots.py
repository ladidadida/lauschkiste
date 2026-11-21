"""CI guard: stored interface snapshots must match the code, with the right version bumps.

After an intended interface change: bump the version, then run
``uv run python -m lauschkiste.contract.snapshots --update`` and commit the snapshot files.
"""

import pytest

from lauschkiste.contract.snapshots import check_target, targets


@pytest.mark.parametrize('target', targets(), ids=lambda t: t.label)
def test_interface_snapshot(target):
    problem = check_target(target)
    assert problem is None, problem



def _bundled_plugins():
    import inspect

    from lauschkiste.contract.manager import discover_plugins
    plugins = [load() for _name, load in sorted(discover_plugins().items())]
    return [cls for cls in plugins if '/packages/plugins/' in inspect.getfile(cls)]


@pytest.mark.parametrize('plugin', _bundled_plugins(), ids=lambda cls: cls.name)
def test_bundled_plugins_accept_the_core_module_versions(plugin):
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version

    from lauschkiste.core_modules import CORE_MODULES

    versions = {cls.name: cls.interface_version for cls in CORE_MODULES}
    requires = plugin.requires if isinstance(plugin.requires, dict) else {}
    for module, spec in requires.items():
        if module in versions and spec:
            assert Version(versions[module]) in SpecifierSet(spec), \
                f"plugin '{plugin.name}' requires '{module}' {spec}, the core has {versions[module]}"
