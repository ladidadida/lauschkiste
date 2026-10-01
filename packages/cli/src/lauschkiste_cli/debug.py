import asyncio
import json
from typing import Optional

import typer
import websockets

app = typer.Typer(help="Developer/debugging tools.")

TOPIC_WIDTH = 40


async def _sniff(port: int, topics: Optional[list[str]]) -> None:
    url = f"ws://localhost:{port}/api/v1/events"
    async with websockets.connect(url) as websocket:
        await websocket.send(json.dumps({'type': 'subscribe', 'topics': topics or ['']}))
        while True:
            message = json.loads(await websocket.recv())
            if message['type'] == 'revoke':
                print(f"{message['topic']:{TOPIC_WIDTH}}: <revoked>")
            else:
                print(f"{message['topic']:{TOPIC_WIDTH}}: {message['data']}")


@app.command()
def sniff(
    port: int = typer.Option(5556, "-p", "--port", help="Connect to the API server on this port"),
    topics: Optional[list[str]] = typer.Option(
        None, "-k", "--topics",
        help="Subscribe to these topic tree(s). If omitted, all topics are subscribed.",
    ),
) -> None:
    """Monitor all messages sent from Jukebox through the publishing interface."""
    try:
        asyncio.run(_sniff(port, topics))
    except KeyboardInterrupt:
        pass
