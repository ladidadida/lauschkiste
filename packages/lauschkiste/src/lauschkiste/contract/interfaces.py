"""Interface snapshots of modules and the framework contract, and the rules for version bumps.

A snapshot is a JSON description of everything another module or plugin can rely on. Comparing
the stored snapshot with the current one tells whether a change is compatible (minor bump) or
breaking (major bump). See documentation/developers/core-and-plugins.md, "Versioning".
"""

import copy
import inspect
import json
import types
import typing
from pathlib import Path
from typing import Any, Dict, List, Tuple, Type

from packaging.version import Version
from pydantic import TypeAdapter

from lauschkiste.contract.declarations import protocol_methods
from lauschkiste.contract.module import Module

EQUAL, MINOR, MAJOR = 'equal', 'minor', 'major'
_RANK = {EQUAL: 0, MINOR: 1, MAJOR: 2}
_ANNOTATION_KEYS = {'title', 'description', 'examples'}


def _inline_refs(schema: Any, defs: Dict[str, Any], depth: int = 0) -> Any:
    if depth > 30:
        return {'recursive': True}
    if isinstance(schema, dict):
        if '$ref' in schema:
            target = defs.get(schema['$ref'].rsplit('/', 1)[-1], {})
            return _inline_refs(target, defs, depth + 1)
        result = {}
        for key, value in schema.items():
            if key == '$defs' or key in _ANNOTATION_KEYS:
                continue
            if key in ('properties', 'patternProperties') and isinstance(value, dict):
                result[key] = {name: _inline_refs(sub, defs, depth + 1) for name, sub in value.items()}
            else:
                result[key] = _inline_refs(value, defs, depth + 1)
        return result
    if isinstance(schema, list):
        return [_inline_refs(item, defs, depth + 1) for item in schema]
    return schema


def normalize_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    return _inline_refs(copy.deepcopy(schema), schema.get('$defs', {}))


def type_schema(tp) -> Dict[str, Any]:
    if tp is type(None):
        return {'type': 'null'}
    return normalize_schema(TypeAdapter(tp).json_schema())


class _Rendered:
    def __init__(self, text: str):
        self.text = text

    def __repr__(self) -> str:
        return self.text


def _format_type(tp) -> str:
    if tp is Ellipsis:
        return '...'
    if isinstance(tp, (list, tuple)):
        return '[' + ', '.join(_format_type(t) for t in tp) + ']'
    origin, args = typing.get_origin(tp), typing.get_args(tp)
    if origin is typing.Union or origin is types.UnionType:
        return ' | '.join('None' if a is type(None) else _format_type(a) for a in args)
    if origin is typing.Literal:
        return f"Literal[{', '.join(repr(a) for a in args)}]"
    if origin is not None and args:
        name = getattr(tp, '_name', None) or inspect.formatannotation(origin)
        return f"{name}[{', '.join(_format_type(a) for a in args)}]"
    return inspect.formatannotation(tp)


def format_signature(func) -> str:
    """``str(inspect.signature(func))``, but rendering unions the same way on every Python version."""
    sig = inspect.signature(func)
    empty = inspect.Parameter.empty

    def render(annotation):
        return annotation if annotation is empty else _Rendered(_format_type(annotation))

    params = [p.replace(annotation=render(p.annotation)) for p in sig.parameters.values()]
    return str(sig.replace(parameters=params, return_annotation=render(sig.return_annotation)))


def describe_module_interface(cls: Type[Module]) -> Dict[str, Any]:
    ops = {}
    for name, op in sorted(cls.operations().items()):
        ops[name] = {
            'kind': op.kind,
            'method': op.spec.method,
            'path': op.path(cls.is_core),
            'args': normalize_schema(op.args_model.model_json_schema()),
            'returns': type_schema(op.return_type),
        }
    events = {name: normalize_schema(spec.model.model_json_schema())
              for name, spec in sorted(cls.events().items())}
    extension_points = {
        name: {m: format_signature(getattr(spec.protocol, m)) for m in protocol_methods(spec.protocol)}
        for name, spec in sorted(cls.extension_point_specs().items())
    }
    return {
        'name': cls.name,
        'kind': 'core' if cls.is_core else 'plugin',
        'interface_version': cls.interface_version,
        'requires': {dep: spec for dep, spec in sorted(cls.required_modules().items())},
        'operations': ops,
        'events': events,
        'extension_points': extension_points,
    }


def describe_contract() -> Dict[str, Any]:
    from lauschkiste.contract import context, declarations, module
    from lauschkiste.contract.version import CONTRACT_VERSION

    def public_api(obj) -> Dict[str, str]:
        api = {}
        for name, value in sorted(vars(obj).items()):
            if name.startswith('_') and name != '__init__':
                continue
            if isinstance(value, (staticmethod, classmethod)):
                value = value.__func__
            if inspect.isfunction(value):
                api[name] = format_signature(value)
            elif isinstance(value, property):
                api[name] = 'property'
            elif not callable(value) and not isinstance(value, (dict, list)):
                api[name] = 'attribute'
        return api

    return {
        'contract_version': CONTRACT_VERSION,
        'Module': public_api(module.Module),
        'Plugin': public_api(module.Plugin),
        'Context': public_api(context.Context),
        'ModuleConfig': public_api(context.ModuleConfig),
        'ExtensionPoint': public_api(declarations.ExtensionPoint),
        'functions': {name: format_signature(getattr(declarations, name))
                      for name in ('action', 'query', 'event', 'extension_point')},
    }


# -- compatibility ------------------------------------------------------------------------------

def _worst(*levels: str) -> str:
    return max(levels, key=_RANK.__getitem__, default=EQUAL)


def _object_parts(schema):
    return schema.get('properties', {}), set(schema.get('required', []))


def _compare_schema(old, new, direction: str, where: str, notes: List[str]) -> str:
    """direction 'input': new must accept all old inputs. 'output': new must give all old guarantees."""
    if old == new:
        return EQUAL
    if isinstance(old, dict) and isinstance(new, dict) and old.get('type') == 'object' == new.get('type'):
        old_props, old_req = _object_parts(old)
        new_props, new_req = _object_parts(new)
        level = EQUAL
        for key, old_sub in old_props.items():
            if key not in new_props:
                notes.append(f"{where}: field '{key}' removed")
                level = MAJOR
                continue
            level = _worst(level, _compare_schema(old_sub, new_props[key], direction, f"{where}.{key}", notes))
        for key in new_props:
            if key not in old_props:
                if direction == 'input' and key in new_req:
                    notes.append(f"{where}: new required field '{key}'")
                    level = MAJOR
                else:
                    notes.append(f"{where}: field '{key}' added")
                    level = _worst(level, MINOR)
        if direction == 'input' and (new_req & set(old_props)) - old_req:
            notes.append(f"{where}: fields became required: {sorted((new_req & set(old_props)) - old_req)}")
            level = MAJOR
        if direction == 'output' and old_req - new_req:
            notes.append(f"{where}: fields became optional: {sorted(old_req - new_req)}")
            level = MAJOR
        rest_old = {k: v for k, v in old.items() if k not in ('properties', 'required')}
        rest_new = {k: v for k, v in new.items() if k not in ('properties', 'required')}
        if rest_old != rest_new:
            notes.append(f"{where}: schema changed")
            level = MAJOR
        return level
    notes.append(f"{where}: type changed")
    return MAJOR


def _compare_named(old: Dict, new: Dict, where: str, notes: List[str], compare) -> str:
    level = EQUAL
    for name in old:
        if name not in new:
            notes.append(f"{where} '{name}' removed")
            level = MAJOR
        else:
            level = _worst(level, compare(old[name], new[name], f"{where} '{name}'"))
    for name in new:
        if name not in old:
            notes.append(f"{where} '{name}' added")
            level = _worst(level, MINOR)
    return level


def compare_module_interfaces(old: Dict[str, Any], new: Dict[str, Any]) -> Tuple[str, List[str]]:
    notes: List[str] = []

    def op(o, n, where):
        level = EQUAL
        for key in ('kind', 'method', 'path'):
            if o[key] != n[key]:
                notes.append(f"{where}: {key} changed from {o[key]!r} to {n[key]!r}")
                level = MAJOR
        level = _worst(level, _compare_schema(o['args'], n['args'], 'input', f"{where} args", notes))
        return _worst(level, _compare_schema(o['returns'], n['returns'], 'output', f"{where} returns", notes))

    def ev(o, n, where):
        return _compare_schema(o, n, 'output', where, notes)

    def ext(o, n, where):
        if o != n:
            notes.append(f"{where}: protocol changed (implementations must be updated)")
            return MAJOR
        return EQUAL

    level = _worst(
        _compare_named(old.get('operations', {}), new.get('operations', {}), 'operation', notes, op),
        _compare_named(old.get('events', {}), new.get('events', {}), 'event', notes, ev),
        _compare_named(old.get('extension_points', {}), new.get('extension_points', {}),
                       'extension point', notes, ext),
    )
    if old.get('requires') != new.get('requires'):
        notes.append("requires changed")
        level = _worst(level, MINOR)
    return level, notes


def compare_contracts(old: Dict[str, Any], new: Dict[str, Any]) -> Tuple[str, List[str]]:
    notes: List[str] = []
    level = EQUAL
    for section in set(old) | set(new):
        if section == 'contract_version':
            continue
        o, n = old.get(section, {}), new.get(section, {})
        for name in o:
            if name not in n:
                notes.append(f"{section}.{name} removed")
                level = MAJOR
            elif o[name] != n[name]:
                notes.append(f"{section}.{name} changed: {o[name]} -> {n[name]}")
                level = MAJOR
        for name in n:
            if name not in o:
                notes.append(f"{section}.{name} added")
                level = _worst(level, MINOR)
    return level, notes


def required_bump_satisfied(level: str, old_version: str, new_version: str) -> bool:
    old_v, new_v = Version(old_version), Version(new_version)
    if level == MAJOR:
        return new_v.major > old_v.major
    if level == MINOR:
        return new_v.major > old_v.major or (new_v.major == old_v.major and new_v.minor > old_v.minor)
    return new_v >= old_v


# -- snapshot files -----------------------------------------------------------------------------

def load_snapshot(path: Path) -> Dict[str, Any]:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def write_snapshot(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write('\n')
