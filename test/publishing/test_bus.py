import logging
import threading
import time

import pytest

from lauschkiste.publishing.bus import EventBus


def test_publish_delivers_to_subscribers_and_updates_cache():
    bus = EventBus()
    received = []
    bus.register(lambda topic, payload: received.append((topic, payload)))

    bus.publish('player.status', {'playing': True})

    assert received == [('player.status', {'playing': True})]
    assert bus.cache_snapshot() == {'player.status': {'playing': True}}


def test_revocation_removes_from_cache_but_is_still_delivered():
    bus = EventBus()
    received = []
    bus.register(lambda topic, payload: received.append((topic, payload)))

    bus.publish('volume.level', 12)
    bus.publish('volume.level', None)

    assert received == [('volume.level', 12), ('volume.level', None)]
    assert bus.cache_snapshot() == {}


def test_unregister_stops_delivery():
    bus = EventBus()
    received = []

    def callback(topic, payload):
        received.append((topic, payload))

    bus.register(callback)
    bus.publish('a', 1)
    bus.unregister(callback)
    bus.publish('a', 2)

    assert received == [('a', 1)]
    assert bus.cache_snapshot() == {'a': 2}


def test_resend_replays_matching_cached_topics_to_all_subscribers():
    bus = EventBus()
    received = []
    bus.publish('player.status', 'playing')
    bus.publish('host.temperature', 42)
    bus.register(lambda topic, payload: received.append((topic, payload)))

    bus.resend('player')

    assert received == [('player.status', 'playing')]


@pytest.mark.parametrize('initial_payload', [None, 47.2])
def test_cache_revocation_is_idempotent(initial_payload):
    bus = EventBus()
    if initial_payload is not None:
        bus.publish('host.temperature.cpu', initial_payload)

    bus.publish('host.temperature.cpu', None)
    bus.publish('host.temperature.cpu', None)

    assert 'host.temperature.cpu' not in bus.cache_snapshot()


def test_publish_is_thread_safe():
    bus = EventBus()
    received = []
    lock = threading.Lock()
    bus.register(lambda topic, payload: (lock.acquire(), received.append(payload), lock.release()))

    def publish_many(start):
        for i in range(start, start + 50):
            bus.publish('counter', i)

    threads = [threading.Thread(target=publish_many, args=(offset,)) for offset in (0, 50, 100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    assert len(received) == 150
    assert bus.cache_snapshot()['counter'] in range(150)


def test_subscriber_error_is_logged_not_raised(caplog):
    bus = EventBus()

    def failing_callback(topic, payload):
        raise ValueError('boom')

    bus.register(failing_callback)
    with caplog.at_level('ERROR', logger='jb.pub.bus'):
        bus.publish('topic', 'payload')  # must not raise

    assert 'boom' in caplog.text or 'failed' in caplog.text


def test_subscriber_error_via_log_handler_does_not_recurse_forever():
    """Reproduces the real hazard: a log handler that republishes ERROR-level records through
    this very bus (see misc/loggingext.py's PubStreamHandler), triggered by the bus's own
    "subscriber callback failed" error log. Without the depth guard, this recurses forever:
    subscriber fails -> bus logs it -> handler republishes -> subscriber fails -> ..."""
    bus = EventBus()
    call_count = []

    class RepublishingHandler(logging.Handler):
        def emit(self, record):
            bus.publish('core.logger', self.format(record))

    logger = logging.getLogger('jb.pub.bus')
    handler = RepublishingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    try:
        def always_fails(topic, payload):
            call_count.append(1)
            raise RuntimeError('always fails')

        bus.register(always_fails)
        start = time.monotonic()
        bus.publish('trigger', 'x')  # must not hang or blow the stack
        assert time.monotonic() - start < 1
        # Exactly 2 invocations: the original 'trigger' publish, plus one nested 'core.logger'
        # republish caused by logging that failure -- then the depth guard stops it recursing.
        assert call_count == [1, 1]
    finally:
        logger.removeHandler(handler)
