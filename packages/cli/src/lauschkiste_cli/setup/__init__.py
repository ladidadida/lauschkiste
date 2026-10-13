"""`lauschctl setup`: prepare this machine for Lauschkiste, step by step and idempotent."""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import typer

import lauschkiste.common.paths
from lauschkiste_cli import plugin
from lauschkiste_cli.setup.base import Answers, Context, Step, ask
from lauschkiste_cli.setup.steps import all_steps, device
from lauschkiste_cli.setup.steps.lauschkiste import public_port
from lauschkiste_cli.setup.system import SetupError, StepSkipped, System


def _select(names: Optional[List[str]], steps: List[Step]) -> List[Step]:
    if not names:
        return steps
    by_name = {step.name: step for step in steps}
    unknown = [name for name in names if name not in by_name and name not in device.all_step_names()]
    if unknown:
        typer.echo(f"Unknown step(s): {', '.join(unknown)}. Steps: {', '.join(by_name)}", err=True)
        raise typer.Exit(2)
    return [step for step in steps if step.name in names]


PHASES = {'device': 'The device and its options', 'peripherals': 'What is attached to it, and its options'}


def _ask_questions(step: Step, ctx: Context, stored: Dict, assume_yes: bool, shown: List[str]) -> None:
    for question in step.questions_for(ctx):
        if not ctx.provides(*question.needs) or (question.when is not None and not question.when(ctx.answers)):
            continue
        if not assume_yes and step.phase not in shown:
            shown.append(step.phase)
            typer.echo(typer.style(f"\n== {PHASES.get(step.phase, step.phase)}", bold=True))
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
    if not check_only and ctx.config_path.exists():
        plugin.rename_in_config(ctx.config_path, plugin.RENAMED_PLUGINS)
    pool = steps or all_steps()
    selected = _select(names, device.with_device_steps(pool, ctx))
    for name in names or ():
        if not any(step.name == name for step in selected):
            typer.echo(f"Skipping '{name}': not applicable on this machine.")
    previous = answers.load()
    shown: List[str] = []
    relevant = []
    index = 0
    while index < len(selected):
        step = selected[index]
        index += 1
        if step.applies(ctx):
            relevant.append(step)
            _ask_questions(step, ctx, previous, ctx.assume_yes, shown)
        elif names:
            typer.echo(f"Skipping '{step.name}': not applicable on this machine.")
        if step.name == 'device':
            done = selected[:index]
            selected = done + [s for s in _select(names, device.with_device_steps(pool, ctx))
                               if not any(s is d for d in done)]

    if not check_only:
        answers.save(_stored_answers(relevant, ctx.answers, previous))

    wanted = [step for step in relevant if step.wanted(ctx)]
    if not check_only and ctx.system.is_debian():
        _install_packages(wanted, ctx)

    return sum(not _run_step(step, ctx, check_only, force) for step in wanted)


def _summary(ctx: Context) -> None:
    """What is left to do and where to go next."""
    for note in ctx.notes:
        typer.echo(f"  - {note}")
    port = public_port(ctx)
    host = ctx.system.output('hostname').strip() or 'localhost'
    typer.echo(f"The web app is at http://{host}{'' if port == 80 else f':{port}'}")


ROOT_NOTE = ("`lauschctl setup` changes the system (packages, services, boot configuration) and uses sudo for that, "
             "so your user needs administrator rights.")


def ensure_root_access(system: System) -> None:
    """Say that sudo is needed; ask for the password once, up front, if sudo wants one."""
    state = system.sudo_state()
    if state in ('root', 'passwordless'):
        return
    typer.echo(typer.style(ROOT_NOTE, bold=True))
    if state == 'missing':
        typer.echo("There is no sudo command. Install it as root (apt install sudo, add your user to the group sudo) "
                   "or run `lauschctl setup` as root.", err=True)
        raise typer.Exit(1)
    if not sys.stdin.isatty():
        typer.echo("sudo asks for a password and there is no terminal to type it in: log in with SSH in a terminal, "
                   "or run `sudo -v` first.", err=True)
        raise typer.Exit(1)
    typer.echo("sudo will ask for your password now (the one of this user); it is not stored.")
    if subprocess.run(['sudo', '-v']).returncode != 0:
        typer.echo("No administrator rights: setup stops. Ask for sudo rights for this user.", err=True)
        raise typer.Exit(1)


def setup(steps: Optional[List[str]] = typer.Argument(None, help="Steps to run (default: all)"),
          check: bool = typer.Option(False, "--check", help="Only report what is missing, change nothing"),
          yes: bool = typer.Option(False, "--yes", "-y", help="Don't ask; reuse earlier answers or defaults"),
          force: bool = typer.Option(False, "--force", help="Apply steps even if they look complete"),
          list_steps: bool = typer.Option(False, "--list", help="List the steps and exit"),
          conf: Optional[Path] = typer.Option(None, "-c", "--conf", envvar=lauschkiste.common.paths.env_name("CONF"),
                                              help="Configuration file")) -> None:
    """Set up this machine for Lauschkiste (packages, service, Samba, hotspot, ...).

    Every step checks first and only changes what is missing, so running it again is safe.
    Answers are kept in $LAUSCHKISTE_HOME/settings/setup.yaml.
    """
    if list_steps:
        listing = Context(system=System(), config_path=conf or lauschkiste.common.paths.config_file())
        for step in device.with_device_steps(all_steps(), listing):
            typer.echo(f"{step.name:12} {step.title}")
        return
    ctx = Context(system=System(), config_path=conf or lauschkiste.common.paths.config_file(),
                  assume_yes=yes)
    if not check:
        ensure_root_access(ctx.system)
    if not steps and not check and not yes:
        typer.echo("This sets up the machine step by step: hardware, system packages, the service and the "
                   "extras you choose. Every question has a default; run it again at any time to change something.")
    failed = run_setup(steps, ctx, Answers(), check_only=check, force=force)
    if failed:
        raise typer.Exit(1)
    if not check:
        typer.echo(typer.style("Setup complete.", fg='green'))
        _summary(ctx)
