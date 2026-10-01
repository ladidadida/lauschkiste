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
