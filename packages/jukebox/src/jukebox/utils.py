"""
Common utility functions
"""
import logging
import os
import subprocess


log = logging.getLogger('jb.utils')


def get_config_action(cfg, section, option, default, valid_actions_dict, logger):
    """
    Looks up the given {section}.{option} config option and returns
    the associated entry from valid_actions_dict, if valid. Falls back to the given
    default otherwise.
    """
    action = str(cfg.getn(section, option, default='')).lower()
    if action not in valid_actions_dict:
        logger.error(f"Config {section}.{option} must be one of {valid_actions_dict.keys()}. Using default '{default}'")
        action = default
    return valid_actions_dict[action]


def get_git_state():
    """Git state of the checkout the jukebox runs from, or a note that it isn't one (package install)."""
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
