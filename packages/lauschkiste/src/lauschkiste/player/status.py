"""Typed player status, independent of the backend that produced it."""

from typing import Any, Dict, Literal, Mapping, Optional

from pydantic import BaseModel


ContentKind = Literal['music', 'audiobook', 'podcast', 'radio']


class PlaybackContext(BaseModel):
    """What is playing: its content type, a title, and the card action that plays it."""
    kind: ContentKind
    title: Optional[str] = None
    action: Optional[str] = None
    args: Dict[str, Any] = {}


class PlayerStatus(BaseModel):
    provider: str
    state: Literal['play', 'pause', 'stop'] = 'stop'
    file: Optional[str] = None
    position: Optional[int] = None
    playlist_length: int = 0
    elapsed: float = 0.0
    duration: Optional[float] = None
    title: Optional[str] = None
    #: Name of a stream (radio station)
    name: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    albumartist: Optional[str] = None
    track: Optional[str] = None
    random: bool = False
    repeat: bool = False
    single: bool = False
    stop_after_current: bool = False
    speed: float = 1.0
    cover_url: Optional[str] = None
    context: Optional[PlaybackContext] = None


def _flag(value: Any) -> bool:
    return str(value).lower() in ('1', 'true', 'on')


def _number(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text(value: Any) -> Optional[str]:
    if value is None or value == '':
        return None
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
        return None if value is None else str(value)
    return str(value)


def status_from_backend(raw: Mapping[str, Any], provider: str) -> PlayerStatus:
    """Build a :class:`PlayerStatus` from a backend's raw (mpd-style) status mapping."""
    state = raw.get('state')
    position = _number(raw.get('song'))
    file = _text(raw.get('file'))
    return PlayerStatus(
        provider=provider,
        state=state if state in ('play', 'pause', 'stop') else 'stop',
        file=file,
        position=int(position) if position is not None and position >= 0 and file else None,
        playlist_length=int(_number(raw.get('playlistlength')) or 0),
        elapsed=_number(raw.get('elapsed')) or 0.0,
        duration=_number(raw.get('duration')),
        title=_text(raw.get('title')),
        name=_text(raw.get('name')),
        artist=_text(raw.get('artist')),
        album=_text(raw.get('album')),
        albumartist=_text(raw.get('albumartist')),
        track=_text(raw.get('track')),
        random=_flag(raw.get('random')),
        repeat=_flag(raw.get('repeat')),
        single=_flag(raw.get('single')),
        speed=_number(raw.get('speed')) or 1.0,
        stop_after_current=_flag(raw.get('stop_after_current')) or raw.get('single') == 'oneshot',
        cover_url=_text(raw.get('cover_url')),
    )
