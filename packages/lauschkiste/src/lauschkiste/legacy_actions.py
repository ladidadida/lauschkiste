"""Conversion of pre-contract commands to action ids.

Before the core/plugin contract, card entries and config actions were stored either as an alias
(``alias: play_card``) or as ``package``/``plugin``/``method`` plus positional ``args`` and
``kwargs``. The contract stores ``action: <module>.<action>`` plus named ``args``.
"""

from typing import Any, Callable, Dict, Mapping, Optional, Tuple

# alias -> (action id, fixed arguments)
ALIASES: Dict[str, Tuple[str, Dict[str, Any]]] = {
    'none': ('system.noop', {}),
    'play_card': ('player.play_card', {}),
    'play_album': ('player.play_album', {}),
    'play_single': ('player.play_single', {}),
    'play_folder': ('player.play_folder', {}),
    'play': ('player.play', {}),
    'pause': ('player.pause', {}),
    'next_song': ('player.next', {}),
    'prev_song': ('player.prev', {}),
    'toggle': ('player.toggle', {}),
    'shuffle': ('player.shuffle', {}),
    'repeat': ('player.repeat', {}),
    'flush_coverart_cache': ('library.flush_covers', {}),
    'set_volume': ('volume.set_volume', {}),
    'change_volume': ('volume.change_volume', {}),
    'set_soft_max_volume': ('volume.set_soft_max_volume', {}),
    'toggle_output': ('volume.toggle_output', {}),
    'shutdown': ('raspberry_pi.shutdown', {}),
    'reboot': ('raspberry_pi.reboot', {}),
    'say_my_ip': ('system.say_my_ip', {}),
    'timer_shutdown': ('timers.start', {'timer': 'shutdown'}),
    'timer_fade_volume': ('timers.start', {'timer': 'fade_volume'}),
    'timer_stop_player': ('timers.start', {'timer': 'stop_player'}),
    'sync_rfidcards_all': ('card_sync.sync_all', {}),
    'sync_rfidcards_change_on_rfid_scan': ('card_sync.sync_change_on_rfid_scan', {}),
}

_PACKAGE_RENAMES = {'misc': 'system', 'sync_rfidcards': 'card_sync'}
_HOST_PLUGIN_ACTIONS = {'shutdown', 'reboot'}
_MISC_RENAMES = {'empty_rpc_call': 'noop'}

CARD_FLAGS = ('ignore_same_id_delay', 'ignore_card_removal_action')


def is_legacy(entry: Mapping) -> bool:
    return not isinstance(entry.get('action'), str)


def _action_from_call(package: str, plugin: Optional[str], method: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    if package == 'host':
        name = plugin if method is None else method
        if name in _HOST_PLUGIN_ACTIONS:
            return f'raspberry_pi.{name}', {}
        return f'system.{name}', {}
    if package == 'timers' and plugin and plugin.startswith('timer_') and method:
        return f'timers.{method}', {'timer': plugin[len('timer_'):]}
    package = _PACKAGE_RENAMES.get(package, package)
    name = method if method is not None else plugin
    if package == 'system':
        name = _MISC_RENAMES.get(name, name)
    return f'{package}.{name}', {}


def _positional(args) -> list:
    if args is None:
        return []
    if isinstance(args, (list, tuple)):
        return list(args)
    return [args]


def convert(entry: Mapping, param_names=None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Convert a legacy command to ``{'action': ..., 'args': {...}}`` (card flags are kept).

    :param param_names: callable ``action_id -> list of parameter names`` or None if unknown;
        needed only to name positional arguments
    :return: ``(converted, None)`` or ``(None, reason)``
    """
    if not is_legacy(entry):
        converted = {'action': entry['action'], 'args': dict(entry.get('args') or {})}
    else:
        alias = entry.get('alias', 'custom')
        if alias is None:
            alias = 'none'
        if alias == 'custom':
            package = entry.get('package')
            if not package:
                return None, "neither 'action', 'alias' nor 'package' given"
            action_id, fixed = _action_from_call(package, entry.get('plugin'), entry.get('method'))
        elif alias in ALIASES:
            action_id, fixed = ALIASES[alias]
        else:
            return None, f"unknown alias '{alias}'"

        args: Dict[str, Any] = dict(fixed)
        kwargs = entry.get('kwargs') or {}
        if not isinstance(kwargs, Mapping):
            return None, f"'kwargs' must be a mapping, got {kwargs!r}"
        positional = _positional(entry.get('args'))
        if positional:
            names = param_names(action_id) if param_names is not None else None
            if names is None:
                return None, f"positional arguments for '{action_id}' can't be named while it is unavailable"
            names = [n for n in names if n not in fixed]
            if len(positional) > len(names):
                return None, f"too many positional arguments for '{action_id}'"
            args.update(zip(names, positional))
        args.update(kwargs)
        converted = {'action': action_id, 'args': args}

    for flag in CARD_FLAGS:
        if flag in entry:
            converted[flag] = entry[flag]
    return converted, None


def bind_action(catalog, entry, where: str, logger) -> Optional[Callable[[], Any]]:
    """A callable running a configured action (either format), or None (logged) if it's invalid."""
    if not isinstance(entry, Mapping):
        logger.error(f"{where}: an action must be a mapping, got {entry!r}")
        return None

    def param_names(action_id):
        return [p.name for p in catalog.operation(action_id).params] if action_id in catalog else None

    converted, problem = convert(entry, param_names)
    if converted is None:
        logger.error(f"{where}: {problem}")
        return None
    try:
        catalog.validate(converted['action'], converted['args'])
    except Exception as error:
        logger.error(f"{where}: {error}")
        return None
    return lambda: catalog.call_ignore_errors(converted['action'], converted['args'])
