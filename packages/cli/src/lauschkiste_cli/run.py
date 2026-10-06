import logging
from pathlib import Path
from typing import Optional

import typer

import lauschkiste.cfghandler
import lauschkiste.paths
from lauschkiste.misc import loggingext

def run(
    conf: Optional[Path] = typer.Option(
        None, "-c", "--conf",
        envvar=lauschkiste.paths.env_name("CONF"),
        file_okay=True, dir_okay=False,
        help="Configuration file (default: $LAUSCHKISTE_HOME/settings/lauschkiste.yaml). Created from "
             "the default template on first run if it doesn't exist yet.",
    ),
    logger_conf: Optional[Path] = typer.Option(
        None, "-l", "--logger",
        envvar=lauschkiste.paths.env_name("LOGGER_CONF"),
        file_okay=True, dir_okay=False,
        help="Logger configuration file (default: $LAUSCHKISTE_HOME/settings/logger.yaml). Created from "
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
    home: Optional[Path] = typer.Option(
        None, "--home", envvar=lauschkiste.paths.env_name("HOME"),
        help="Directory with all data (settings, music, logs). "
             "Default: $XDG_DATA_HOME/lauschkiste (~/.local/share/lauschkiste).",
    ),
) -> None:
    """Run the Lauschkiste server."""
    if home is not None:
        lauschkiste.paths.set_home(home)
    if verbose and quiet:
        raise typer.BadParameter("--verbose and --quiet are mutually exclusive")
    conf = conf or lauschkiste.paths.config_file()
    logger_conf = logger_conf or lauschkiste.paths.settings_dir() / 'logger.yaml'

    if verbose:
        logger = loggingext.configure_default({1: logging.INFO, 2: logging.DEBUG}[min(verbose, 2)],
                                               with_publisher=True)
        if verbose < 3:
            loggingext.configure_default(logging.ERROR, name='lauschkiste.plugin.call', with_publisher=True)
    elif quiet:
        logger = loggingext.configure_default({1: logging.ERROR, 2: logging.CRITICAL}[min(quiet, 2)],
                                               with_publisher=True)
    else:
        lauschkiste.cfghandler.ensure_default_config(
            str(logger_conf), str(lauschkiste.paths.resource('default-settings', 'logger.default.yaml')))
        logger = loggingext.configure_from_file(str(logger_conf))

    logger.info(f"Home '{lauschkiste.paths.home()}', configuration file '{conf}'")
    from lauschkiste.startup import import_fastapi
    import_fastapi()
    from lauschkiste.daemon import get_daemon  # heavy (web server); only `run` needs it

    daemon = get_daemon(str(conf), artifacts)
    daemon.run()
