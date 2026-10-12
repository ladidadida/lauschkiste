import json

from lauschkiste.common.statefile import StateDict


def test_state_dict_saves_only_changes(tmp_path):
    path = tmp_path / 'sub' / 'state.json'
    state = StateDict(path)
    assert state == {}
    state.save()
    assert not path.exists()
    state['folder'] = 'a'
    state.save()
    assert json.loads(path.read_text()) == {'folder': 'a'}
    mtime = path.stat().st_mtime_ns
    state.save()
    assert path.stat().st_mtime_ns == mtime
    assert StateDict(path) == {'folder': 'a'}


def test_state_dict_ignores_a_broken_file(tmp_path):
    path = tmp_path / 'state.json'
    path.write_text('{ nope')
    assert StateDict(path) == {}
