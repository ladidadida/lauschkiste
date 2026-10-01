import logging
from pathlib import Path
from typing import Optional

import typer

import jukebox.cfghandler
import jukebox.paths
from jukebox.misc import loggingext

def run(
    conf: Optional[Path] = typer.Option(
        None, "-c", "--conf",
        envvar="JUKEBOX_CONF",
        file_okay=True, dir_okay=False,
        help="Jukebox configuration file (default: $JUKEBOX_HOME/settings/jukebox.yaml). Created from "
             "the default template on first run if it doesn't exist yet.",
    ),
    logger_conf: Optional[Path] = typer.Option(
        None, "-l", "--logger",
        envvar="JUKEBOX_LOGGER_CONF",
        file_okay=True, dir_okay=False,
        help="Logger configuration file (default: $JUKEBOX_HOME/settings/logger.yaml). Created from "
             "the default template on first run if it doesn't exist yet.",
    ),
    verbose: int = typer.Option(
        0, "-v", "--verbose", count=True,
        help="Increase logger verbosity from warning to info (-v) to debug (-vv) to see all "
             "plugin calls and not only errors (-vvv)",
    ),
    quiet: int = typer.Option(
        0, "-q", "--quiet", count=True,
        help="Decrease logger verbosity from warning to error (-q) to critical (-qq)",
    ),
    artifacts: bool = typer.Option(
        False, "-a", "--artifacts",
        help="Write out all artifacts and auto-generated help files",
    ),
) -> None:
    """Start the Jukebox Daemon."""
    if verbose and quiet:
        raise typer.BadParameter("--verbose and --quiet are mutually exclusive")
    conf = conf or jukebox.paths.settings_dir() / 'jukebox.yaml'
    logger_conf = logger_conf or jukebox.paths.settings_dir() / 'logger.yaml'

    if verbose:
        logger = loggingext.configure_default({1: logging.INFO, 2: logging.DEBUG}[min(verbose, 2)],
                                               with_publisher=True)
        if verbose < 3:
            loggingext.configure_default(logging.ERROR, name='jb.plugin.call', with_publisher=True)
    elif quiet:
        logger = loggingext.configure_default({1: logging.ERROR, 2: logging.CRITICAL}[min(quiet, 2)],
                                               with_publisher=True)
    else:
        jukebox.cfghandler.ensure_default_config(
            str(logger_conf), str(jukebox.paths.resource('default-settings', 'logger.default.yaml')))
        logger = loggingext.configure_from_file(str(logger_conf))

    logger.info(f"Jukebox home '{jukebox.paths.home()}', configuration file '{conf}'")
    from jukebox.daemon import get_jukebox_daemon  # heavy (web server); only `run` needs it

    myjukebox = get_jukebox_daemon(str(conf), artifacts)
    myjukebox.run()
