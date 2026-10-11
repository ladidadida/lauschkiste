"""Building blocks of `lauschctl setup`: questions, steps, the answers file."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, List, Optional, Sequence, Tuple

import typer
from ruamel.yaml import YAML

import lauschkiste.common.cfghandler
import lauschkiste.common.paths
from lauschkiste_cli.setup.system import System


@dataclass(frozen=True)
class Question:
    key: str
    text: str
    #: Value or ``callable(ctx)``
    default: Any = None
    #: 'bool', 'text', 'secret' (secrets are not stored) or 'choice'
    kind: str = 'bool'
    #: For 'choice': ``((value, label), ...)`` or ``callable(ctx)`` returning it
    choices: Any = ()
    #: Only asked if ``when(answers)`` is true
    when: Optional[Callable[[Dict[str, Any]], Any]] = None
    #: Returns an error message for an invalid text answer
    validate: Optional[Callable[[str], Optional[str]]] = None
    #: Text shown above the question, or ``callable(ctx)`` returning it
    help: Any = ''

    def default_for(self, ctx: 'Context') -> Any:
        return self.default(ctx) if callable(self.default) else self.default

    def choices_for(self, ctx: 'Context') -> Sequence[Tuple[str, str]]:
        return tuple(self.choices(ctx) if callable(self.choices) else self.choices)


@dataclass
class Context:
    system: System
    config_path: Path
    answers: Dict[str, Any] = field(default_factory=dict)
    assume_yes: bool = False
    #: Things to tell the user at the end (a reboot is needed, ...)
    notes: List[str] = field(default_factory=list)

    def answer(self, key: str, default: Any = None) -> Any:
        return self.answers.get(key, default)

    def load_config(self) -> lauschkiste.common.cfghandler.ConfigHandler:
        lauschkiste.common.cfghandler.ensure_default_config(
            str(self.config_path), str(lauschkiste.common.paths.resource('default-settings', 'lauschkiste.default.yaml')))
        cfg = lauschkiste.common.cfghandler.ConfigHandler('setup')
        lauschkiste.common.cfghandler.load_yaml(cfg, str(self.config_path))
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
    help_text = question.help(ctx) if callable(question.help) else question.help
    if help_text:
        typer.echo(typer.style(help_text, dim=True))
    if question.kind == 'bool':
        return typer.confirm(question.text, default=bool(default))
    if question.kind == 'choice':
        return _choose(question, ctx, default)
    while True:
        value = typer.prompt(question.text, default=default, hide_input=question.kind == 'secret',
                             show_default=question.kind != 'secret')
        problem = question.validate(value) if question.validate else None
        if not problem:
            return value
        typer.echo(problem)


def _choose(question: Question, ctx: Context, default: Any) -> str:
    choices = question.choices_for(ctx)
    values = [value for value, _ in choices]
    typer.echo(question.text)
    for number, (_, label) in enumerate(choices, 1):
        typer.echo(f"  {number}) {label}")
    preset = str(values.index(default) + 1) if default in values else '1'
    while True:
        answer = str(typer.prompt('Number', default=preset)).strip()
        if answer in values:
            return answer
        if answer.isdigit() and 1 <= int(answer) <= len(values):
            return values[int(answer) - 1]
        typer.echo(f"Please enter a number from 1 to {len(values)}.")


class Answers:
    """``$LAUSCHKISTE_HOME/settings/setup.yaml``: the answers of earlier runs."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or lauschkiste.common.paths.settings_dir() / 'setup.yaml'

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
            stream.write('# Answers of `lauschctl setup`, reused by `lauschctl setup --yes`\n')
            yaml.dump(dict(sorted(answers.items())), stream)
