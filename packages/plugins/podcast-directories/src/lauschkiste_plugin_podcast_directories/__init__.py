"""Find podcasts in directories and subscribe to them.

Each directory can be switched off and has the settings that matter for it::

    plugins:
      podcast_directories:
        fyyd: {enabled: false}
        itunes: {country: AT}

Another directory needs code: a plugin that registers an object with ``search(term, limit)`` and
``top(limit)`` at ``podcasts.directories``.
"""

import logging
from typing import List

from pydantic import BaseModel, Field

from lauschkiste.contract import Plugin
from lauschkiste_plugin_podcast_directories.directories import Fyyd, ITunes, PodcastIndex

logger = logging.getLogger('lauschkiste.podcast_directories')


class AppleSettings(BaseModel):
    enabled: bool = Field(True, title='Search in Apple Podcasts')
    country: str = Field('DE', title='Country', description='Two letters; decides the popular podcasts')


class FyydSettings(BaseModel):
    enabled: bool = Field(True, title='Search in fyyd')
    language: str = Field('de', title='Language of the popular podcasts')


class PodcastIndexSettings(BaseModel):
    enabled: bool = Field(False, title='Search in the Podcast Index',
                          description='Needs a free key and secret from podcastindex.org (below)')
    language: str = Field('de', title='Language of the popular podcasts')


class PodcastDirectoriesSettings(BaseModel):
    itunes: AppleSettings = Field(default_factory=AppleSettings, title='Apple Podcasts')
    fyyd: FyydSettings = Field(default_factory=FyydSettings, title='fyyd')
    podcastindex: PodcastIndexSettings = Field(default_factory=PodcastIndexSettings, title='Podcast Index')
    podcastindex_key: str = Field('', title='Podcast Index API key', json_schema_extra={'secret': True},
                                  description='Leave empty to keep the current one.')
    podcastindex_secret: str = Field('', title='Podcast Index API secret', json_schema_extra={'secret': True},
                                     description='Leave empty to keep the current one.')


class PodcastDirectories(Plugin):
    """Search for podcasts in Apple Podcasts, fyyd and the Podcast Index."""

    name = 'podcast_directories'
    interface_version = '1.0'
    requires = {'podcasts': '>=3.0,<4'}
    settings = PodcastDirectoriesSettings

    def __init__(self):
        self._registered: List[str] = []

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._register()

    def settings_changed(self, changed) -> bool:
        self._register()
        return True

    def _register(self) -> None:
        points = self._ctx.modules.podcasts.directories
        for key in self._registered:
            points.unregister(key)
        self._registered = []
        config = self._ctx.config

        def setting(directory, name, default):
            return config.get(directory, name, default=default)

        if setting('itunes', 'enabled', True):
            points.register('itunes', ITunes('Apple Podcasts', country=setting('itunes', 'country', 'DE')))
            self._registered.append('itunes')
        if setting('fyyd', 'enabled', True):
            points.register('fyyd', Fyyd('fyyd', language=setting('fyyd', 'language', 'de')))
            self._registered.append('fyyd')
        if setting('podcastindex', 'enabled', False):
            points.register('podcastindex', PodcastIndex(
                'Podcast Index', language=setting('podcastindex', 'language', 'de'),
                key=lambda: config.get('podcastindex_key', default=''),
                secret=lambda: config.get('podcastindex_secret', default='')))
            self._registered.append('podcastindex')
