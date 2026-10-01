# -*- coding: utf-8 -*-
"""Transport-neutral pieces of the browser events-over-websocket bridge.

Split out of the old Tornado bridge (`lauschkiste.api.server`, removed once `lauschkiste.api.fastapi_server`
became the sole HTTP/WebSocket bridge) so nothing here depends on a specific web framework.
"""

MAX_MESSAGE_SIZE = 1024 * 1024


class EventBroker:
    """Maintain browser subscriptions, backed by the shared :class:`lauschkiste.publishing.bus.EventBus`.

    Register :meth:`publish` as a bus subscriber callback (``bus.register(broker.publish)``); the
    bus already delivers `payload=None` for revocations and calls this from whatever thread
    published, so no separate transport bridging is needed here.
    """

    def __init__(self, bus=None):
        self._bus = bus
        self.clients = set()

    def register(self, client):
        self.clients.add(client)

    def unregister(self, client):
        self.clients.discard(client)

    @staticmethod
    def _matches(topic, subscriptions):
        return any(topic.startswith(prefix) for prefix in subscriptions)

    def subscribe(self, client, topics):
        client.subscriptions.update(topics)
        if self._bus is None:
            return
        for topic, data in self._bus.cache_snapshot().items():
            if self._matches(topic, topics):
                self._send(client, {
                    'type': 'event',
                    'topic': topic,
                    'data': data,
                })

    @staticmethod
    def unsubscribe(client, topics):
        client.subscriptions.difference_update(topics)

    def publish(self, topic, payload):
        """Bus subscriber callback. `payload=None` means the topic was revoked."""
        if payload is None:
            outgoing = {'type': 'revoke', 'topic': topic}
        else:
            outgoing = {'type': 'event', 'topic': topic, 'data': payload}

        for client in tuple(self.clients):
            if self._matches(topic, client.subscriptions):
                self._send(client, outgoing)

    def _send(self, client, message):
        try:
            future = client.write_message(message)
        except Exception:
            # Transport-neutral: covers any transport's synchronous "client is gone" signal.
            self.unregister(client)
            return

        if future is not None:
            future.add_done_callback(lambda completed: completed.exception())


def parse_subscription_command(command):
    """Validate a decoded events-websocket command.

    :return: ``(command_type, topics)``
    :raises ValueError: if the command is not a well-formed subscribe/unsubscribe request
    """
    if not isinstance(command, dict):
        raise ValueError('Commands must be objects.')

    command_type = command.get('type')
    topics = command.get('topics')
    if (
        command_type not in ('subscribe', 'unsubscribe')
        or not isinstance(topics, list)
        or any(not isinstance(topic, str) for topic in topics)
    ):
        raise ValueError('Invalid subscription command.')

    return command_type, topics
