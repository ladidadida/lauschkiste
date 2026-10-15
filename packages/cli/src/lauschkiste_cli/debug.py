import asyncio
import json
import re
import subprocess
from typing import List, Optional, Tuple

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
    """Monitor all messages Lauschkiste publishes (events)."""
    try:
        asyncio.run(_sniff(port, topics))
    except KeyboardInterrupt:
        pass


BOOT_PROCESSES = ('Xorg', 'X', 'openbox', 'chromium', 'chromium-browse')
START_UP_LINE = re.compile(r'Start-up: .*')


def _run(*command: str) -> str:
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=15).stdout
    except (OSError, subprocess.SubprocessError):
        return ''


def _uptime() -> Optional[float]:
    try:
        with open('/proc/uptime') as stream:
            return float(stream.read().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def monotonic_seconds(output: str) -> Optional[float]:
    """Seconds after boot from ``systemctl show -p <Name>Monotonic`` output; None if the unit never got there."""
    match = re.search(r'=(\d+)', output)
    if not match or int(match.group(1)) == 0:
        return None
    return int(match.group(1)) / 1_000_000


def process_starts(ps_output: str, uptime: float) -> List[Tuple[float, str]]:
    """(seconds after boot, name) of the screen's processes from ``ps -eo etimes=,comm=``."""
    starts = []
    for line in ps_output.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0].isdigit() and parts[1].strip() in BOOT_PROCESSES:
            starts.append((uptime - int(parts[0]), parts[1].strip()))
    return starts


def boot_events() -> List[Tuple[float, str]]:
    uptime = _uptime()
    if uptime is None:
        return []
    events = []
    for unit, label in (('NetworkManager-wait-online.service', 'network online'),
                        ('systemd-networkd-wait-online.service', 'network online')):
        seconds = monotonic_seconds(_run('systemctl', 'show', unit, '-p', 'ActiveEnterTimestampMonotonic'))
        if seconds:
            events.append((seconds, label))
    seconds = monotonic_seconds(_run('systemctl', '--user', 'show', 'lauschkiste.service', '-p',
                                     'ActiveEnterTimestampMonotonic'))
    if seconds:
        events.append((seconds, 'lauschkiste.service started'))
    log = _run('journalctl', '--user', '-u', 'lauschkiste.service', '-b', '-o', 'cat', '--no-pager')
    ready = re.findall(r'ready at boot \+ ([\d.]+) s', log)
    if ready:
        events.append((float(ready[-1]), 'Lauschkiste ready (API listening)'))
    events.extend((at, f"{name} started") for at, name in process_starts(_run('ps', '-eo', 'etimes=,comm='), uptime))
    return sorted(events)


@app.command()
def boot() -> None:
    """Show what happened since boot and when: kernel, network, Lauschkiste, the screen's browser."""
    summary = _run('systemd-analyze').strip()
    if summary:
        print(summary)
        print()
    events = boot_events()
    if not events:
        print("No boot information available (needs Linux with systemd).")
        return
    for seconds, label in events:
        print(f"boot + {seconds:6.1f} s  {label}")
    uptime = _uptime()
    if uptime is not None:
        print(f"boot + {uptime:6.1f} s  now")
    line = START_UP_LINE.findall(_run('journalctl', '--user', '-u', 'lauschkiste.service', '-b', '-o', 'cat',
                                      '--no-pager'))
    if line:
        print()
        print(line[-1])
