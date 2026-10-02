"""The volume core module: volume, mute, soft maximum, output selection and fade-out.

The mixer is PulseAudio/PipeWire (via pulsectl) when a server is reachable, otherwise the volume of
the active player backend.
"""

import logging
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from pydantic import BaseModel

from lauschkiste.contract import CoreModule, OperationError, action, event, query

logger = logging.getLogger('lauschkiste.volume')


class Output(BaseModel):
    name: str
    alias: str
    active: bool


class VolumeState(BaseModel):
    volume: int
    mute: bool
    soft_max_volume: int


class OutputsState(BaseModel):
    active: Optional[str] = None
    outputs: List[Output]


@dataclass
class OutputConfig:
    key: str
    alias: str
    sink_name: Optional[str]
    volume_limit: int


class Mixer(Protocol):
    def get(self) -> int: ...

    def set(self, volume: int) -> None: ...

    def is_muted(self) -> bool: ...

    def set_mute(self, mute: bool) -> None: ...

    def outputs(self) -> List[Output]: ...

    def set_output(self, name: str) -> None: ...


class PlayerMixer:
    """Volume of the active player backend; no outputs to choose from."""

    def __init__(self, player):
        self._player = player
        self._muted_volume: Optional[int] = None

    def get(self) -> int:
        return 0 if self._muted_volume is not None else self._player.get_volume().volume

    def set(self, volume: int) -> None:
        self._muted_volume = None
        self._player.set_volume(volume)

    def is_muted(self) -> bool:
        return self._muted_volume is not None

    def set_mute(self, mute: bool) -> None:
        if mute and self._muted_volume is None:
            self._muted_volume = self._player.get_volume().volume
            self._player.set_volume(0)
        elif not mute and self._muted_volume is not None:
            volume, self._muted_volume = self._muted_volume, None
            self._player.set_volume(volume)

    def outputs(self) -> List[Output]:
        return [Output(name='player', alias='Player', active=True)]

    def set_output(self, name: str) -> None:
        if name != 'player':
            raise OperationError(404, 'unknown_output', f"Unknown output '{name}'")


class PulseMixer:
    """PulseAudio/PipeWire default sink; ``volume_limit`` of an output scales 0..100 to 0..limit."""

    def __init__(self, outputs: List[OutputConfig]):
        import pulsectl
        self._pulsectl = pulsectl
        self._outputs = outputs
        with self._client() as pulse:
            default = pulse.server_info().default_sink_name
        for output in self._outputs:
            if output.sink_name is None and output is self._outputs[0]:
                output.sink_name = default

    def _client(self):
        return self._pulsectl.Pulse('lauschkiste-volume')

    def _limit(self, sink_name: str) -> float:
        for output in self._outputs:
            if output.sink_name == sink_name:
                return output.volume_limit / 100.0
        return 1.0

    def _sink(self, pulse):
        return pulse.get_sink_by_name(pulse.server_info().default_sink_name)

    def get(self) -> int:
        with self._client() as pulse:
            sink = self._sink(pulse)
            return int(round(100 * pulse.volume_get_all_chans(sink) / self._limit(sink.name)))

    def set(self, volume: int) -> None:
        with self._client() as pulse:
            sink = self._sink(pulse)
            pulse.mute(sink, mute=False)
            pulse.volume_set_all_chans(sink, volume / 100.0 * self._limit(sink.name))

    def is_muted(self) -> bool:
        with self._client() as pulse:
            return bool(self._sink(pulse).mute)

    def set_mute(self, mute: bool) -> None:
        with self._client() as pulse:
            pulse.mute(self._sink(pulse), mute=mute)

    def outputs(self) -> List[Output]:
        with self._client() as pulse:
            default = pulse.server_info().default_sink_name
            available = {sink.name for sink in pulse.sink_list()}
        return [Output(name=o.key, alias=o.alias, active=o.sink_name == default)
                for o in self._outputs if o.sink_name in available]

    def set_output(self, name: str) -> None:
        output = next((o for o in self._outputs if o.key == name), None)
        if output is None or output.sink_name is None:
            raise OperationError(404, 'unknown_output', f"Unknown output '{name}'")
        with self._client() as pulse:
            try:
                sink = pulse.get_sink_by_name(output.sink_name)
            except Exception:
                raise OperationError(409, 'output_unavailable',
                                     f"Output '{output.alias}' ({output.sink_name}) is not connected") from None
            pulse.default_set(sink)
            for stream in pulse.sink_input_list():
                try:
                    pulse.sink_input_move(stream.index, sink.index)
                except Exception as error:
                    logger.debug(f"Could not move stream {stream.index}: {error}")


def _setting(ctx, *keys, default=None):
    return ctx.config.get(*keys, default=default)


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


class Volume(CoreModule):
    """Volume, mute, soft maximum and audio output."""

    name = 'volume'
    interface_version = '1.0'
    requires = ('player',)

    level = event('level', VolumeState)
    outputs_changed = event('outputs', OutputsState)

    def __init__(self):
        self._ctx = None
        self._mixer: Optional[Mixer] = None
        self._soft_max = 100
        self._fade_cancel = threading.Event()
        self._fade_executor = None

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._soft_max = _clamp(_setting(ctx, 'soft_max_volume', default=100), 0, 100)
        self._mixer = self._create_mixer(_setting(ctx, 'mixer', default='auto'))
        self._fade_executor = ctx.executor('fade')

    def ready(self) -> None:
        startup = _setting(self._ctx, 'startup_volume', default=None)
        if startup is not None:
            self.set_volume(int(startup))
        else:
            self._publish()
        self._publish_outputs()

    def _create_mixer(self, choice: str) -> Mixer:
        if choice in ('auto', 'pulse'):
            try:
                outputs = self._configured_outputs()
                mixer = PulseMixer(outputs)
                logger.info("Volume mixer: PulseAudio/PipeWire")
                return mixer
            except Exception as error:
                if choice == 'pulse':
                    logger.error(f"PulseAudio/PipeWire not available ({error}); using the player's volume")
                else:
                    logger.info(f"No PulseAudio/PipeWire server ({error.__class__.__name__}); "
                                f"using the player's volume")
        return PlayerMixer(self._ctx.modules.player)

    def _configured_outputs(self) -> List[OutputConfig]:
        configured: Dict[str, Any] = _setting(self._ctx, 'outputs', default=None) or {'primary': {}}
        return [OutputConfig(key=key, alias=str(values.get('alias', key)),
                             sink_name=values.get('pulse_sink_name'),
                             volume_limit=_clamp(values.get('volume_limit', 100), 1, 100))
                for key, values in configured.items()]

    def _state(self) -> VolumeState:
        muted = self._mixer.is_muted()
        return VolumeState(volume=0 if muted else self._mixer.get(), mute=muted, soft_max_volume=self._soft_max)

    def _publish(self) -> VolumeState:
        state = self._state()
        self._ctx.publish(self.level, state)
        return state

    def _publish_outputs(self) -> OutputsState:
        outputs = self._mixer.outputs()
        state = OutputsState(active=next((o.name for o in outputs if o.active), None), outputs=outputs)
        self._ctx.publish(self.outputs_changed, state)
        return state

    # -- operations -----------------------------------------------------------------------------

    @query(path='')
    def get_volume(self) -> VolumeState:
        """Current volume, mute state and soft maximum."""
        return self._state()

    @action(method='PUT', path='')
    def set_volume(self, volume: int) -> VolumeState:
        """Set the volume (0-100, limited to the soft maximum)."""
        self._fade_cancel.set()
        self._mixer.set(_clamp(volume, 0, self._soft_max))
        return self._publish()

    @action(path='/change')
    def change_volume(self, step: int = 5) -> VolumeState:
        """Change the volume by ``step`` (negative to lower it)."""
        return self.set_volume(self._mixer.get() + step)

    @action(path='/mute')
    def mute(self, mute: Optional[bool] = None) -> VolumeState:
        """Mute or unmute; toggles when ``mute`` is left out."""
        self._mixer.set_mute(not self._mixer.is_muted() if mute is None else mute)
        return self._publish()

    @action(method='PUT', path='/soft-max')
    def set_soft_max_volume(self, max_volume: int) -> VolumeState:
        """Limit the volume that can be set (0-100); lowers the current volume if needed."""
        self._soft_max = _clamp(max_volume, 0, 100)
        self._ctx.config.set('soft_max_volume', value=self._soft_max)
        if self._mixer.get() > self._soft_max:
            self._mixer.set(self._soft_max)
        return self._publish()

    @query(path='/outputs')
    def get_outputs(self) -> OutputsState:
        """Configured outputs that are available right now."""
        outputs = self._mixer.outputs()
        return OutputsState(active=next((o.name for o in outputs if o.active), None), outputs=outputs)

    @action(method='PUT', path='/outputs/active')
    def set_output(self, name: str) -> OutputsState:
        """Switch the audio output."""
        self._mixer.set_output(name)
        if self._mixer.get() > self._soft_max:
            self._mixer.set(self._soft_max)
        self._publish()
        return self._publish_outputs()

    @action(path='/outputs/toggle')
    def toggle_output(self) -> OutputsState:
        """Switch to the next available output."""
        outputs = self._mixer.outputs()
        if len(outputs) < 2:
            return self._publish_outputs()
        current = next((i for i, o in enumerate(outputs) if o.active), -1)
        return self.set_output(outputs[(current + 1) % len(outputs)].name)

    @action(path='/fade-out')
    def fade_out(self, seconds: float = 10.0) -> None:
        """Lower the volume to zero over ``seconds``, stop playback, then restore the volume."""
        self._fade_cancel.set()
        cancel = threading.Event()
        self._fade_cancel = cancel
        start = self._mixer.get()
        steps = max(1, int(seconds * 4))

        def run():
            for step in range(1, steps + 1):
                if cancel.wait(seconds / steps):
                    return
                with self._ctx.lock:
                    self._mixer.set(int(start * (1 - step / steps)))
            self._ctx.modules.player.stop()
            with self._ctx.lock:
                self._mixer.set(start)
                self._publish()

        self._fade_executor.submit(run)
