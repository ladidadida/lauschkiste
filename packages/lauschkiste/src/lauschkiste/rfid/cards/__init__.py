"""The RFID card database: which action a card triggers.

Entries are stored as ``action: <module>.<action>`` plus named ``args``.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel

import lauschkiste.cfghandler
import lauschkiste.paths
from lauschkiste.contract import ActionError, CoreModule, OperationError, action, event, query

log = logging.getLogger('lauschkiste.cards')
cfg_cards = lauschkiste.cfghandler.get_handler('cards')

DEFAULT_DATABASE = 'settings/cards.yaml'


class CardEntry(BaseModel):
    action: str
    args: Dict[str, Any] = {}
    ignore_same_id_delay: bool = False
    ignore_card_removal_action: bool = False


class CardInfo(BaseModel):
    action: Optional[str] = None
    args: Dict[str, Any] = {}
    ignore_same_id_delay: bool = False
    ignore_card_removal_action: bool = False
    description: str = ''
    error: Optional[str] = None


class CardsChanged(BaseModel):
    changed_at: str


class Cards(CoreModule):
    """Card database: register, list and delete cards."""

    name = 'cards'
    interface_version = '1.0'

    changed = event('changed', CardsChanged)

    def __init__(self):
        self._ctx = None
        self._path = DEFAULT_DATABASE

    # -- lifecycle ------------------------------------------------------------------------------

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._path = str(lauschkiste.paths.resolve(ctx.config.get('database', default=DEFAULT_DATABASE)))
        try:
            cfg_cards.load(self._path)
        except FileNotFoundError:
            cfg_cards.config_dict({})
            log.warning(f"Card database file not found. Creating empty database: '{self._path}'")
            cfg_cards.save(only_if_changed=False)
        with cfg_cards:
            illegal = [key for key in cfg_cards.keys() if not isinstance(key, str)]
        if illegal:
            log.error(f"Ignoring non-string card IDs in the card database: {illegal}")
        self._announce_change()

    def stop(self):
        cfg_cards.save(only_if_changed=True)
        return []

    def _announce_change(self) -> None:
        self._ctx.publish(self.changed, CardsChanged(changed_at=datetime.now(timezone.utc).isoformat()))

    # -- helpers --------------------------------------------------------------------------------

    def _check(self, entry: Any):
        """Return ``(CardEntry or None, error or None)`` for a stored entry."""
        if not isinstance(entry, dict):
            return None, 'invalid entry'
        try:
            card = CardEntry.model_validate(entry)
        except Exception as error:
            return None, f'invalid entry: {error}'
        try:
            self._ctx.actions.validate(card.action, card.args)
        except ActionError as error:
            return card, str(error)
        return card, None

    def _description(self, action_id: Optional[str]) -> str:
        if action_id is None or action_id not in self._ctx.actions:
            return ''
        doc = self._ctx.actions.operation(action_id).func.__doc__ or ''
        return doc.strip().split('\n\n', 1)[0]

    # -- operations -----------------------------------------------------------------------------

    @query(path='/api/v1/cards')
    def list_cards(self) -> Dict[str, CardInfo]:
        """All registered cards with their action and whether it is currently available."""
        with cfg_cards:
            items = [(card_id, entry) for card_id, entry in cfg_cards.items() if isinstance(card_id, str)]
        result = {}
        for card_id, entry in items:
            card, error = self._check(entry)
            if card is None:
                result[card_id] = CardInfo(error=error)
            else:
                result[card_id] = CardInfo(**card.model_dump(), description=self._description(card.action),
                                           error=error)
        return result

    @query(path='/api/v1/cards/{card_id}')
    def get_card(self, card_id: str) -> Optional[CardEntry]:
        """The card's entry, or null when it is unknown or its action is unavailable."""
        with cfg_cards:
            entry = cfg_cards.get(card_id, default=None)
        if entry is None:
            return None
        card, error = self._check(entry)
        if error is not None:
            log.warning(f"Card '{card_id}': {error}")
            return None
        return card

    @action(path='/api/v1/cards')
    def register_card(self, card_id: str, action: str, args: Optional[Dict[str, Any]] = None,
                      ignore_same_id_delay: bool = False, ignore_card_removal_action: bool = False,
                      overwrite: bool = False) -> None:
        """Register a card to trigger an action."""
        args = dict(args or {})
        try:
            self._ctx.actions.validate(action, args)
        except ActionError as error:
            raise OperationError(422, 'invalid_action', str(error)) from None
        entry = CardEntry(action=action, args=args, ignore_same_id_delay=ignore_same_id_delay,
                          ignore_card_removal_action=ignore_card_removal_action)
        with cfg_cards:
            if not overwrite and card_id in cfg_cards.keys():
                raise OperationError(409, 'card_exists', f"Card '{card_id}' is already registered")
            cfg_cards[card_id] = entry.model_dump()
            cfg_cards.save()
        self._announce_change()

    @action(method='DELETE', path='/api/v1/cards/{card_id}')
    def delete_card(self, card_id: str) -> None:
        """Delete a card."""
        with cfg_cards:
            if card_id not in cfg_cards.keys():
                raise OperationError(404, 'unknown_card', f"Card '{card_id}' is not registered")
            del cfg_cards[card_id]
            cfg_cards.save()
        self._announce_change()
