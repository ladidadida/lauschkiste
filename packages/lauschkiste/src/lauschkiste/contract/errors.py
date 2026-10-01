class ContractError(Exception):
    """A module violates the contract (declaration, dependency or version problem)."""


class OperationError(Exception):
    """Raised by an operation to report a client error with an HTTP status and error code."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


class ActionError(Exception):
    """An action id or its arguments are invalid."""
