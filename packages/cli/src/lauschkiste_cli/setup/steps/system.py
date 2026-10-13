"""Operating system: packages and the login message."""

from typing import List

import lauschkiste.common.paths
from lauschkiste_cli.setup.base import Question, Step
from lauschkiste_cli.setup.steps.lauschkiste import public_port

BUILD_PACKAGES = ['build-essential', 'python3-dev', 'libffi-dev']
RUNTIME_PACKAGES = ['alsa-utils', 'espeak', 'libportaudio2']
#: A desktop brings its own sound server; a Pi Lite image does not
AUDIO_PACKAGES = ['pipewire', 'pipewire-pulse', 'pipewire-audio', 'wireplumber', 'libspa-0.2-bluetooth']
#: piwheels' `av` (32-bit ARM) links against the system's ffmpeg libraries instead of bundling them
PIWHEELS_ARCHITECTURES = ('armv6', 'armv7')


class PackagesStep(Step):
    name = 'packages'
    title = 'System packages'
    questions = (
        Question('upgrade_os', 'Upgrade all operating system packages now (takes a while)?', default=False,
                 needs=('system_setup',)),
    )

    def relevant(self, ctx):
        return ctx.system.is_debian()

    def packages(self, ctx):
        audio = AUDIO_PACKAGES if ctx.provides('system_setup') else []
        ffmpeg = ['ffmpeg'] if ctx.system.architecture() in PIWHEELS_ARCHITECTURES else []
        return [*BUILD_PACKAGES, *RUNTIME_PACKAGES, *audio, *ffmpeg]

    def apply(self, ctx):
        pass


class WelcomeStep(Step):
    name = 'welcome'
    title = 'Login message'
    needs = ('system_setup',)
    TARGET = '/etc/update-motd.d/99-lauschkiste-welcome'

    def _content(self, ctx) -> str:
        port = public_port(ctx)
        return lauschkiste.common.paths.resource('system', '99-lauschkiste-welcome').read_text().replace('@PORT@', str(port))

    def check(self, ctx) -> List[str]:
        return [] if ctx.system.read(self.TARGET) == self._content(ctx) else ['login message not installed or outdated']

    def apply(self, ctx):
        ctx.system.write(self.TARGET, self._content(ctx), root=True, mode=0o755)
