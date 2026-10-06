"""The hardware core module: the active board, which pins and buses are used by whom, and power.

Board-neutral: a board support plugin registers at ``hardware.boards`` and describes its pins and
interfaces; modules using pins or buses register at ``hardware.claims``. See
documentation/developers/hardware.md.
"""

import logging
from typing import Any, Dict, List, Optional, Protocol, Tuple

from pydantic import BaseModel

import lauschkiste.contract.plugins as plugins
from lauschkiste.contract import CoreModule, OperationError, action, extension_point, query

logger = logging.getLogger('lauschkiste.hardware')


class Claim(BaseModel):
    """A resource (pin or interface) a module uses; buses like I²C can be shared."""
    resource: str
    owner: str
    purpose: str = ''
    shared: bool = False


class Usage(BaseModel):
    owner: str
    purpose: str = ''


class PinInfo(BaseModel):
    id: str
    label: str
    position: Optional[int] = None
    functions: List[str] = []
    used_by: List[Usage] = []
    conflict: bool = False


class InterfaceInfo(BaseModel):
    id: str
    label: str
    pins: List[str] = []
    used_by: List[Usage] = []


class DetectedBoard(BaseModel):
    name: str
    model: str


class HardwareState(BaseModel):
    board: Optional[str] = None
    model: Optional[str] = None
    pins: List[PinInfo] = []
    interfaces: List[InterfaceInfo] = []
    conflicts: List[str] = []
    unknown: List[Claim] = []
    boot_pending: List[str] = []
    detected: List[DetectedBoard] = []


class Choice(BaseModel):
    value: str
    label: str


class GpioLine(BaseModel):
    chip: int
    line: int


class Board(Protocol):
    def describe(self) -> Dict[str, Any]:
        """``{'name', 'model', 'pins': [{'id', 'label', 'position', 'functions'}],
        'interfaces': [{'id', 'label', 'pins'}]}``"""

    def pin_id(self, value: Any) -> Optional[str]:
        """The board's id of a pin given as the user wrote it (e.g. ``17`` or ``'GPIO17'``), None if unknown."""

    def gpio_line(self, pin: str) -> Tuple[int, int]:
        """(gpiochip number, line) of a GPIO pin."""

    def shutdown(self) -> None: ...

    def reboot(self) -> None: ...

    def boot_pending(self) -> List[str]:
        """Settings that need the boot configuration changed (``lauschctl setup``) and a reboot."""


class ClaimProvider(Protocol):
    def claims(self) -> List[Claim]: ...


class Hardware(CoreModule):
    """The board Lauschkiste runs on, its pins and who uses them; shutdown and reboot."""

    name = 'hardware'
    interface_version = '1.1'
    concurrency = 'threadsafe'

    boards = extension_point('boards', Board)
    claims = extension_point('claims', ClaimProvider)

    def __init__(self):
        self._ctx: Any = None

    def start(self, ctx) -> None:
        self._ctx = ctx

    def ready(self) -> None:
        names = self.boards.names()
        if len(names) > 1:
            logger.error(f"More than one board plugin is enabled ({', '.join(names)}); using '{names[0]}'")

    # -- helpers --------------------------------------------------------------------------------

    def _board(self) -> Optional[Any]:
        names = self.boards.names()
        return self.boards.get(names[0]) if names else None

    def _require_board(self):
        board = self._board()
        if board is None:
            raise OperationError(501, 'no_board', 'No board support plugin is enabled')
        return board

    def _claims(self) -> List[Claim]:
        result = []
        for name, provider in self.claims.items():
            try:
                result.extend(Claim.model_validate(claim) for claim in provider.claims() or [])
            except Exception as error:
                logger.warning(f"Claims of '{name}' are not available: {error}")
        return result

    def state(self) -> HardwareState:
        board = self._board()
        if board is None:
            return HardwareState(unknown=self._claims(), detected=plugins.detected_boards())
        description = board.describe()
        pins = {pin['id']: PinInfo.model_validate(pin) for pin in description.get('pins', [])}
        interfaces = {entry['id']: InterfaceInfo.model_validate(entry) for entry in description.get('interfaces', [])}
        shared: Dict[str, List[bool]] = {}
        unknown = []
        for claim in self._claims():
            usage = Usage(owner=claim.owner, purpose=claim.purpose)
            if claim.resource in interfaces:
                interface = interfaces[claim.resource]
                interface.used_by.append(usage)
                targets = interface.pins
                claim_shared = True
            else:
                pin = board.pin_id(claim.resource)
                if pin is None or pin not in pins:
                    unknown.append(claim)
                    continue
                targets = [pin]
                claim_shared = claim.shared
            for pin in targets:
                if pin in pins and usage not in pins[pin].used_by:
                    pins[pin].used_by.append(usage)
                    shared.setdefault(pin, []).append(claim_shared)
        conflicts = []
        for pin_id, pin in pins.items():
            owners = {usage.owner for usage in pin.used_by}
            if len(pin.used_by) > 1 and not all(shared.get(pin_id, [])) and len(owners) > 1:
                pin.conflict = True
                conflicts.append(pin_id)
        try:
            pending = list(board.boot_pending() or [])
        except Exception as error:
            logger.debug(f"Boot configuration not checked: {error}")
            pending = []
        return HardwareState(board=description.get('name'), model=description.get('model'),
                             pins=list(pins.values()), interfaces=list(interfaces.values()),
                             conflicts=conflicts, unknown=unknown, boot_pending=pending)

    # -- operations -----------------------------------------------------------------------------

    @query(path='/')
    def get_state(self) -> HardwareState:
        """The board, its pins and interfaces, who uses them, conflicts and pending boot changes."""
        return self.state()

    @query(path='/pin-options')
    def pin_options(self) -> List[Choice]:
        """GPIO pins of the board for choosing in settings, with their current users."""
        state = self.state()
        options = []
        for pin in state.pins:
            if 'gpio' not in pin.functions:
                continue
            users = ', '.join(f'{u.owner}: {u.purpose}' if u.purpose else u.owner for u in pin.used_by)
            options.append(Choice(value=pin.id, label=f'{pin.label} – {users}' if users else pin.label))
        return options

    @query(path='/gpio-line')
    def gpio_line(self, pin: str) -> GpioLine:
        """GPIO chip and line of a pin (for device plugins)."""
        board = self._require_board()
        pin_id = board.pin_id(pin)
        if pin_id is None:
            raise OperationError(404, 'unknown_pin', f"Pin '{pin}' does not exist on this board")
        chip, line = board.gpio_line(pin_id)
        return GpioLine(chip=chip, line=line)

    @action()
    def shutdown(self) -> None:
        """Shut the box down."""
        self._require_board().shutdown()

    @action()
    def reboot(self) -> None:
        """Reboot the box."""
        self._require_board().reboot()
