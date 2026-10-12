"""The git state of a source checkout."""

import logging
import os
import subprocess

log = logging.getLogger('lauschkiste.common.gitstate')


def get_git_state():
    """Git state of the checkout Lauschkiste runs from, or a note that it isn't one (package install)."""
    source_dir = os.path.dirname(os.path.abspath(__file__))

    def git(*args):
        return subprocess.run(['git', *args], cwd=source_dir, capture_output=True, text=True,
                              check=True, timeout=5).stdout.strip()

    try:
        gitlog = git('log', '--pretty=%h [%cs] %s %d', '-n', '1', '--no-color')
        describe = git('describe', '--always', '--dirty')
    except (OSError, subprocess.SubprocessError) as error:
        log.debug(f"No git state: {error}")
        return "not a git checkout"
    return f"{gitlog} [{describe}]"
