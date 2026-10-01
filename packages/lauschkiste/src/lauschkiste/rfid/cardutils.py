"""Readable descriptions of card database entries."""

from typing import Any, List, Mapping

import lauschkiste.cfghandler

cfg_cards = lauschkiste.cfghandler.get_handler('cards')


def card_command_to_str(entry: Mapping[str, Any], long: bool = False) -> List[str]:
    """``[action(args)]``, plus the card flags when ``long`` is set."""
    action = entry.get('action')
    if not isinstance(action, str):
        return ["Old card format (not migrated yet)"]
    args = ', '.join(f"{k}={v!r}" for k, v in (entry.get('args') or {}).items())
    readable = [f"{action}({args})"]
    if long:
        for flag in ('ignore_same_id_delay', 'ignore_card_removal_action'):
            if flag in entry:
                readable.append(f"{flag}: {entry[flag]}")
    return readable


def card_to_str(card_id: str, long: bool = False) -> List[str]:
    entry = cfg_cards.getn(card_id, default=None)
    if not isinstance(entry, Mapping):
        return ["Error: Card ID not found in database!"]
    return card_command_to_str(entry, long)
