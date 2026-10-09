"""Asking several directories at once and merging what they answer (podcast and radio directories)."""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from lauschkiste.contract import OperationError

logger = logging.getLogger('lauschkiste.directories')

Row = Dict[str, Any]


def ask(directories: Iterable[Tuple[str, Any]], only: Optional[str], call: Callable[[Any], List[Row]],
        what: str) -> Tuple[List[Tuple[str, List[Row]]], Dict[str, str]]:
    """Ask all directories (or just ``only``) in parallel with ``call(directory)``.

    Returns the rows of each directory and, for a directory that failed, why; one failing leaves the others."""
    wanted = [(key, item) for key, item in directories if only in (None, key)]
    if only and not wanted:
        raise OperationError(404, 'unknown_directory', f"No {what} directory '{only}'")

    def run(entry):
        key, item = entry
        try:
            return key, call(item), None
        except Exception as error:
            return key, [], f'{error.__class__.__name__}: {error}'

    answers: List[Tuple[str, List[Row]]] = []
    errors: Dict[str, str] = {}
    if wanted:
        with ThreadPoolExecutor(max_workers=len(wanted)) as pool:
            for key, rows, error in pool.map(run, wanted):
                if error:
                    errors[key] = error
                    logger.warning(f"{what.capitalize()} directory '{key}': {error}")
                answers.append((key, rows))
    return answers, errors


def interleave(answers: List[Tuple[str, List[Row]]], key_of: Callable[[Row], str], usable: Callable[[Row], bool],
               limit: Optional[int] = None) -> List[Row]:
    """One list from the answers: the directories take turns (so that none fills it), duplicates (same ``key_of``)
    are dropped, and every row gets the id of the directory it came from as ``directory``."""
    rows_by_directory = [[{**row, 'directory': key} for row in rows if usable(row)] for key, rows in answers]
    seen, merged = set(), []
    for rank in range(max((len(rows) for rows in rows_by_directory), default=0)):
        for rows in rows_by_directory:
            if rank < len(rows):
                key = key_of(rows[rank])
                if key not in seen:
                    seen.add(key)
                    merged.append(rows[rank])
    return merged[:limit] if limit else merged
