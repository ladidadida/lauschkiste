from typing import Optional, Protocol

import pytest
from pydantic import BaseModel

from lauschkiste.contract import CoreModule, action, event, extension_point, query
from lauschkiste.contract.interfaces import (
    EQUAL, MAJOR, MINOR, compare_module_interfaces, describe_module_interface, required_bump_satisfied,
)


class Status(BaseModel):
    state: str
    elapsed: float


class StatusMore(BaseModel):
    state: str
    elapsed: float
    title: Optional[str] = None


class StatusLess(BaseModel):
    state: str


class Backend(Protocol):
    def play(self) -> None: ...


class Backend2(Protocol):
    def play(self) -> None: ...

    def stop(self) -> None: ...


def module(ops=None, events=None, extensions=None):
    attrs = {'name': 'player'}
    attrs.update(ops or {})
    attrs.update(events or {})
    attrs.update(extensions or {})
    return describe_module_interface(type('Player', (CoreModule,), attrs))


def op_play(folder: str) -> None: ...


def op_play_optional(folder: str, recursive: bool = False) -> None: ...


def op_play_required(folder: str, recursive: bool) -> None: ...


def op_play_int(folder: int) -> None: ...


def op_other(folder: str) -> None: ...


def op_play_moved(folder: str) -> None: ...


def base():
    return module({'play_folder': action()(op_play)}, {'status': event('status', Status)})


@pytest.mark.parametrize('new, expected', [
    (base, EQUAL),
    (lambda: module({'play_folder': action()(op_play_optional)}, {'status': event('status', Status)}), MINOR),
    (lambda: module({'play_folder': action()(op_play_required)}, {'status': event('status', Status)}), MAJOR),
    (lambda: module({'play_folder': action()(op_play_int)}, {'status': event('status', Status)}), MAJOR),
    (lambda: module({'play_folder': action(path='/play_folder')(op_play_moved)},
                    {'status': event('status', Status)}), EQUAL),
    (lambda: module({'play_folder': action(path='/folder')(op_play_moved)},
                    {'status': event('status', Status)}), MAJOR),
    (lambda: module({}, {'status': event('status', Status)}), MAJOR),
    (lambda: module({'play_folder': action()(op_play), 'other': query()(op_other)},
                    {'status': event('status', Status)}), MINOR),
    (lambda: module({'play_folder': action()(op_play)}, {'status': event('status', StatusMore)}), MINOR),
    (lambda: module({'play_folder': action()(op_play)}, {'status': event('status', StatusLess)}), MAJOR),
    (lambda: module({'play_folder': action()(op_play)}, {}), MAJOR),
])
def test_compare(new, expected):
    level, notes = compare_module_interfaces(base(), new())
    assert level == expected, notes


def test_extension_point_protocol_changes_are_breaking():
    old = module(extensions={'backends': extension_point('backends', Backend)})
    new = module(extensions={'backends': extension_point('backends', Backend2)})
    assert compare_module_interfaces(old, new)[0] == MAJOR


@pytest.mark.parametrize('level, old, new, ok', [
    (EQUAL, '1.2', '1.2', True),
    (MINOR, '1.2', '1.2', False),
    (MINOR, '1.2', '1.3', True),
    (MINOR, '1.2', '2.0', True),
    (MAJOR, '1.2', '1.3', False),
    (MAJOR, '1.2', '2.0', True),
])
def test_required_bump(level, old, new, ok):
    assert required_bump_satisfied(level, old, new) is ok
