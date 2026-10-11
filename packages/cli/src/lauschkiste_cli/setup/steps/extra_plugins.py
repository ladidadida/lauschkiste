"""Plugins from other sources (PyPI, GitHub, a URL or a file): installed and enabled during the setup."""

import importlib
import re
from typing import Dict, List, Optional

import typer
from packaging.requirements import InvalidRequirement, Requirement

import lauschkiste.contract.plugins as plugins
import lauschkiste.common.paths
import lauschkiste.common.statefile
from lauschkiste_cli import plugin
from lauschkiste_cli.setup.base import Context, Question, Step
from lauschkiste_cli.setup.system import SetupError

GITHUB = re.compile(r'^github:([\w.-]+)/([\w.-]+)(?:@([\w./-]+))?$')
STATE_FILE = 'extra_plugins.json'


def parse_spec(text: str) -> str:
    """One entry as pip takes it; ``github:owner/repo@ref`` becomes a git URL. Raises ``ValueError``."""
    if text.startswith('-'):
        raise ValueError(f"'{text}': options are not allowed")
    github = GITHUB.match(text)
    if github:
        owner, repo, ref = github.groups()
        return f"git+https://github.com/{owner}/{repo}" + (f"@{ref}" if ref else '')
    if text.startswith(('https://', 'git+https://')) or text.startswith(('/', './', '~/')):
        return text
    try:
        Requirement(text)
    except InvalidRequirement:
        raise ValueError(f"'{text}' is neither a package name, a github:owner/repo link nor a URL") from None
    return text


def parse_specs(text: str) -> List[str]:
    return [parse_spec(part) for part in re.split(r'[\s,]+', text.strip()) if part]


def _validate(text: str) -> Optional[str]:
    try:
        parse_specs(text)
    except ValueError as error:
        return str(error)
    return None


def _specs(ctx: Context) -> List[str]:
    return parse_specs(str(ctx.answer('extra_plugins', '') or ''))


def _state_path():
    return lauschkiste.common.paths.settings_dir() / STATE_FILE


def _state() -> Dict[str, List[str]]:
    return {key: list(value) for key, value in lauschkiste.common.statefile.read_json(_state_path()).items()}


class ExtraPluginsStep(Step):
    name = 'extra_plugins'
    title = 'Plugins from other sources'
    questions = (
        Question('extra_plugins', 'Further plugins to install (package names, github:owner/repo[@tag] or URLs, '
                 'separated by spaces; empty for none)', kind='text', default='', validate=_validate,
                 help='A plugin runs with the rights of your user: install only what you trust, and pin a version or '
                      'tag.'),
    )

    def wanted(self, ctx):
        return bool(_specs(ctx))

    def packages(self, ctx):
        return ['git'] if any(spec.startswith('git+') for spec in _specs(ctx)) else []

    def check(self, ctx):
        state, enabled = _state(), ctx.enabled_plugins()
        problems = []
        for spec in _specs(ctx):
            if spec not in state:
                problems.append(f"'{spec}' is not installed")
            problems += [f"plugin '{name}' of '{spec}' is not enabled" for name in state.get(spec, [])
                         if name not in enabled]
        return problems

    def apply(self, ctx):
        state = _state()
        for spec in _specs(ctx):
            if spec not in state:
                if not ctx.assume_yes and not typer.confirm(f"Install '{spec}'? It runs with your user's rights."):
                    continue
                typer.echo(f"    installing {spec}")
                before = set(plugins.installed())
                try:
                    plugin.install_requirements([spec])
                except Exception as error:
                    raise SetupError(f"could not install '{spec}': {error}") from None
                importlib.invalidate_caches()
                state[spec] = sorted(set(plugins.installed()) - before)
                lauschkiste.common.statefile.write_json(_state_path(), state)
                if not state[spec]:
                    typer.echo(f"    '{spec}' provides no plugins (or they were installed already).")
            self._enable(ctx, state.get(spec, []))

    def _enable(self, ctx: Context, names: List[str]) -> None:
        enabled = ctx.enabled_plugins()
        cfg = ctx.load_config()
        for name in names:
            if name in enabled:
                continue
            reason = plugins.why_not_enable(cfg, name)
            if reason:
                typer.echo(f"    can't enable '{name}': {reason}")
                continue
            extras = plugin.plugin_extras(name)
            if extras:
                plugin.install_requirements(extras)
            plugin.add_to_config(ctx.config_path, [name])
            typer.echo(f"    enabled '{name}'")
