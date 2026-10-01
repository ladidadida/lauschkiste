"""Building blocks of `jukebox setup`: questions, steps, the answers file."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, List, Optional, Sequence, Tuple

import typer
from ruamel.yaml import YAML

import lauschkiste.cfghandler
import lauschkiste.paths
from lauschkiste_cli.setup.system import System


@dataclass(frozen=True)
class Question:
    key: str
    text: str
    #: Value or ``callable(ctx)``
    default: Any = None
    #: 'bool', 'text' or 'secret' (secrets are not stored)
    kind: str = 'bool'
    #: Only asked if ``when(answers)`` is true
    when: Optional[Callable[[Dict[str, Any]], Any]] = None
    #: Returns an error message for an invalid text answer
    validate: Optional[Callable[[str], Optional[str]]] = None
    help: str = ''

    def default_for(self, ctx: 'Context') -> Any:
        return self.default(ctx) if callable(self.default) else self.default


@dataclass
class Context:
    system: System
    config_path: Path
    answers: Dict[str, Any] = field(default_factory=dict)
    assume_yes: bool = False

    def answer(self, key: str, default: Any = None) -> Any:
        return self.answers.get(key, default)

    def load_config(self) -> lauschkiste.cfghandler.ConfigHandler:
        lauschkiste.cfghandler.ensure_default_config(
            str(self.config_path), str(lauschkiste.paths.resource('default-settings', 'lauschkiste.default.yaml')))
        cfg = lauschkiste.cfghandler.ConfigHandler('setup')
        lauschkiste.cfghandler.load_yaml(cfg, str(self.config_path))
        return cfg

    def enabled_plugins(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {}
        plugins = self.load_config().getn('plugins', default=None)
        return dict(plugins) if isinstance(plugins, dict) else {}


class Step:
    name: ClassVar[str]
    title: ClassVar[str]
    questions: ClassVar[Tuple[Question, ...]] = ()

    def relevant(self, ctx: Context) -> bool:
        """Does the step make sense on this machine at all?"""
        return True

    def wanted(self, ctx: Context) -> bool:
        """Did the user choose it (from the answers)?"""
        return True

    def packages(self, ctx: Context) -> Sequence[str]:
        """Debian packages the step needs (installed before any step is applied)."""
        return ()

    def prepare(self, ctx: Context) -> None:
        """Runs before the packages are installed."""

    def check(self, ctx: Context) -> List[str]:
        """What's missing; empty if the step is applied."""
        return []

    def apply(self, ctx: Context) -> None:
        raise NotImplementedError


def ask(question: Question, ctx: Context, stored: Dict[str, Any], assume_yes: bool) -> Any:
    default = stored.get(question.key, question.default_for(ctx))
    if assume_yes:
        return default
    if question.help:
        typer.echo(typer.style(question.help, dim=True))
    if question.kind == 'bool':
        return typer.confirm(question.text, default=bool(default))
    while True:
        value = typer.prompt(question.text, default=default, hide_input=question.kind == 'secret',
                             show_default=question.kind != 'secret')
        problem = question.validate(value) if question.validate else None
        if not problem:
            return value
        typer.echo(problem)


class Answers:
    """``$LAUSCHKISTE_HOME/settings/setup.yaml``: the answers of earlier runs."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or lauschkiste.paths.settings_dir() / 'setup.yaml'

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        data = YAML(typ='safe').load(self.path.read_text())
        return dict(data) if isinstance(data, dict) else {}

    def save(self, answers: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        yaml = YAML()
        yaml.default_flow_style = False
        with self.path.open('w') as stream:
            stream.write('# Answers of `jukebox setup`, reused by `jukebox setup --yes`\n')
            yaml.dump(dict(sorted(answers.items())), stream)
