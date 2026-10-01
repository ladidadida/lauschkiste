"""The process-wide event bus. Modules publish through their ``Context``, not directly."""

from lauschkiste.publishing.bus import EventBus

_BUS = EventBus()


def get_bus() -> EventBus:
    """The shared, thread-safe event bus."""
    return _BUS
