import pytest

import lauschkiste.paths


@pytest.fixture(autouse=True)
def isolated_home(tmp_path_factory, monkeypatch):
    """Every test gets its own LAUSCHKISTE_HOME, so nothing is written to a real one."""
    home = tmp_path_factory.mktemp('home')
    monkeypatch.setenv(lauschkiste.paths.HOME_ENV, str(home))
    lauschkiste.paths.set_home(None)
    yield home
    lauschkiste.paths.set_home(None)
