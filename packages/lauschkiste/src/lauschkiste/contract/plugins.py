"""Installed plugins: their extras, whether those are installed, and enabling them in the config."""

from importlib.metadata import PackageNotFoundError, distribution, entry_points
from typing import Any, Dict, List

from packaging.markers import default_environment
from packaging.requirements import Requirement

ENTRY_POINT_GROUP = 'lauschkiste.plugins'


def installed() -> Dict[str, Any]:
    """Entry points of the installed plugins by name."""
    return {ep.name: ep for ep in entry_points(group=ENTRY_POINT_GROUP)}


def load(ep):
    """(plugin class, None) or (None, reason it can't be imported)."""
    try:
        return ep.load(), None
    except Exception as error:
        return None, f"{error.__class__.__name__}: {error}"


def plugin_extras(name: str) -> List[str]:
    """Requirements for the extras plugin ``name`` declares, e.g. ``['pkg[gpio]']``."""
    ep = installed().get(name)
    if ep is None or ep.dist is None:
        return []
    cls, _ = load(ep)
    extras = tuple(getattr(cls, 'extras', ()) or ()) if cls is not None else ()
    return [f"{ep.dist.name}[{','.join(extras)}]"] if extras else []


def missing_extras(name: str) -> List[str]:
    """``plugin_extras(name)`` whose dependencies are not (all) installed in this environment."""
    missing = []
    for requirement in plugin_extras(name):
        wanted = Requirement(requirement)
        try:
            declared = distribution(wanted.name).requires or []
        except PackageNotFoundError:
            missing.append(requirement)
            continue
        for extra in wanted.extras:
            environment = {**default_environment(), 'extra': extra}
            for line in declared:
                dependency = Requirement(line)
                if dependency.marker is None or not dependency.marker.evaluate(environment):
                    continue
                try:
                    distribution(dependency.name)
                except PackageNotFoundError:
                    missing.append(requirement)
                    break
            else:
                continue
            break
    return missing


def enabled(cfg) -> Dict[str, Any]:
    plugins = cfg.getn('plugins', default=None)
    return plugins if isinstance(plugins, dict) else {}


def set_enabled(cfg, name: str, on: bool) -> bool:
    """Enable or disable ``name`` in the config (disabling drops its settings); True if it changed."""
    with cfg:
        current = enabled(cfg)
        if on == (name in current):
            return False
        if on:
            cfg.setn('plugins', name, value={})
        else:
            del current[name]
    return True


def describe(cfg, manager=None) -> List[Dict[str, Any]]:
    """Installed (and enabled but missing) plugins: package, summary, enabled, running, problem, missing extras."""
    available = installed()
    on = enabled(cfg)
    result = []
    for name in sorted(set(available) | set(on)):
        ep = available.get(name)
        entry: Dict[str, Any] = {'name': name, 'enabled': name in on, 'running': bool(manager and name in manager),
                                 'package': None, 'version': None, 'summary': '', 'problem': None,
                                 'missing_extras': []}
        if ep is None:
            entry['problem'] = 'not installed'
        else:
            cls, problem = load(ep)
            if ep.dist is not None:
                entry['package'], entry['version'] = ep.dist.name, ep.dist.version
            entry['summary'] = (getattr(cls, '__doc__', None) or '').strip().split('\n', 1)[0].replace('``', '') if cls else ''
            entry['problem'] = problem or (manager.failed.get(name) if manager else None)
            entry['missing_extras'] = missing_extras(name)
        result.append(entry)
    return result
