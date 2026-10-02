"""`lauschctl setup`: prepare this machine for Lauschkiste, step by step and idempotent."""

from pathlib import Path
from typing import Dict, List, Optional

import typer

import lauschkiste.paths
from lauschkiste_cli.setup.base import Answers, Context, Step, ask
from lauschkiste_cli.setup.steps import all_steps
from lauschkiste_cli.setup.system import SetupError, StepSkipped, System


def _select(names: Optional[List[str]], steps: List[Step]) -> List[Step]:
    if not names:
        return steps
    by_name = {step.name: step for step in steps}
    unknown = [name for name in names if name not in by_name]
    if unknown:
        typer.echo(f"Unknown step(s): {', '.join(unknown)}. Steps: {', '.join(by_name)}", err=True)
        raise typer.Exit(2)
    return [step for step in steps if step.name in names]


def _ask_questions(steps: List[Step], ctx: Context, stored: Dict, assume_yes: bool) -> None:
    for step in steps:
        for question in step.questions:
            if question.when is None or question.when(ctx.answers):
                ctx.answers[question.key] = ask(question, ctx, stored, assume_yes)


def _stored_answers(steps: List[Step], answers: Dict, previous: Dict) -> Dict:
    secret = {q.key for step in steps for q in step.questions if q.kind == 'secret'}
    return {key: value for key, value in {**previous, **answers}.items() if key not in secret}


def _install_packages(steps: List[Step], ctx: Context) -> None:
    wanted = list(dict.fromkeys(package for step in steps for package in step.packages(ctx)))
    missing = ctx.system.missing_packages(wanted) if wanted else []
    upgrade = bool(ctx.answer('upgrade_os')) and any(step.name == 'packages' for step in steps)
    if not missing and not upgrade:
        return
    for step in steps:
        step.prepare(ctx)
    apt = ['env', 'DEBIAN_FRONTEND=noninteractive', 'apt-get', '-y']
    ctx.system.run(*apt, '-qq', 'update', root=True)
    if upgrade:
        ctx.system.run(*apt, 'full-upgrade', root=True)
    if missing:
        ctx.system.run(*apt, 'install', '--no-install-recommends', *missing, root=True)


def _run_step(step: Step, ctx: Context, check_only: bool, force: bool) -> bool:
    """True if the step is complete afterwards (or was skipped)."""
    missing = ctx.system.missing_packages(step.packages(ctx)) if step.packages(ctx) else []
    problems = [f'package {package} is not installed' for package in missing] + step.check(ctx)
    if check_only or (not problems and not force):
        status = typer.style('ok', fg='green') if not problems else typer.style('to do', fg='yellow')
        typer.echo(f"[{status}] {step.name}: {step.title}")
        for problem in problems:
            typer.echo(f"         - {problem}")
        return not problems
    typer.echo(typer.style(f"==> {step.name}: {step.title}", bold=True))
    try:
        step.apply(ctx)
        remaining = step.check(ctx)
    except StepSkipped as reason:
        typer.echo(typer.style(f"    skipped: {reason}", fg='yellow'))
        return True
    except SetupError as error:
        remaining = [str(error)]
    if remaining:
        typer.echo(typer.style(f"    '{step.name}' is not complete:", fg='red'))
        for problem in remaining:
            typer.echo(f"      - {problem}")
    return not remaining


def run_setup(names: Optional[List[str]], ctx: Context, answers: Answers, check_only: bool = False,
              force: bool = False, steps: Optional[List[Step]] = None) -> int:
    """Returns the number of steps with remaining problems."""
    selected = _select(names, steps or all_steps())
    relevant = []
    for step in selected:
        if step.relevant(ctx):
            relevant.append(step)
        elif names:
            typer.echo(f"Skipping '{step.name}': not applicable on this machine.")

    previous = answers.load()
    _ask_questions(relevant, ctx, previous, ctx.assume_yes)
    if not check_only:
        answers.save(_stored_answers(relevant, ctx.answers, previous))

    wanted = [step for step in relevant if step.wanted(ctx)]
    if not check_only and ctx.system.is_debian():
        _install_packages(wanted, ctx)

    return sum(not _run_step(step, ctx, check_only, force) for step in wanted)


def setup(steps: Optional[List[str]] = typer.Argument(None, help="Steps to run (default: all)"),
          check: bool = typer.Option(False, "--check", help="Only report what is missing, change nothing"),
          yes: bool = typer.Option(False, "--yes", "-y", help="Don't ask; reuse earlier answers or defaults"),
          force: bool = typer.Option(False, "--force", help="Apply steps even if they look complete"),
          list_steps: bool = typer.Option(False, "--list", help="List the steps and exit"),
          conf: Optional[Path] = typer.Option(None, "-c", "--conf", envvar=lauschkiste.paths.env_name("CONF"),
                                              help="Configuration file")) -> None:
    """Set up this machine for Lauschkiste (packages, service, Samba, hotspot, ...).

    Every step checks first and only changes what is missing, so running it again is safe.
    Answers are kept in $LAUSCHKISTE_HOME/settings/setup.yaml.
    """
    if list_steps:
        for step in all_steps():
            typer.echo(f"{step.name:12} {step.title}")
        return
    ctx = Context(system=System(), config_path=conf or lauschkiste.paths.config_file(),
                  assume_yes=yes)
    failed = run_setup(steps, ctx, Answers(), check_only=check, force=force)
    if failed:
        raise typer.Exit(1)
    if not check:
        typer.echo(typer.style("Setup complete.", fg='green'))
