"""Find podcasts and radio stations in directories and add them.

Each directory can be switched off and has the settings that matter for it::

    plugins:
      podcast_directories:
        fyyd: {enabled: false}
        itunes: {country: AT}

Another directory needs code: a plugin that registers an object with ``search(term, limit)`` and
``top(limit)`` at ``podcasts.directories``.
"""

import logging
from typing import List, Literal, get_args

from pydantic import BaseModel, Field

from lauschkiste.contract import Plugin
from lauschkiste_plugin_directories.directories import Fyyd, ITunes, PodcastIndex, RadioBrowser

logger = logging.getLogger('lauschkiste.podcast_directories')


Country = Literal['de', 'at', 'ch', 'us', 'gb', 'fr', 'it', 'es', 'nl', 'be', 'dk', 'se', 'no', 'fi', 'pl', 'cz',
                  'pt', 'ie', 'ca', 'au']
Language = Literal['de', 'en', 'fr', 'it', 'es', 'nl', 'pl', 'tr']
COUNTRIES = get_args(Country)
LANGUAGES = get_args(Language)


class AppleSettings(BaseModel):
    enabled: bool = Field(True, title='Search in Apple Podcasts', description='What you type is sent to Apple')
    country: Country = Field('de', title='Country', description='Decides which podcasts are popular')


class FyydSettings(BaseModel):
    enabled: bool = Field(True, title='Search in fyyd', description='What you type is sent to fyyd.de')
    language: Language = Field('de', title='Language of the popular podcasts')


class PodcastIndexSettings(BaseModel):
    enabled: bool = Field(False, title='Search in the Podcast Index',
                          description='Needs a free key and secret from podcastindex.org (below)')
    language: Language = Field('de', title='Language of the popular podcasts')


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
    title = 'Find podcasts'
    interface_version = '1.1'
    requires = {'podcasts': '>=4.0,<5'}
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
            points.register('itunes', ITunes('Apple Podcasts', country=setting('itunes', 'country', 'de')))
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


class RadioBrowserSettings(BaseModel):
    enabled: bool = Field(True, title='Search in radio-browser.info',
                          description='What you type is sent to radio-browser.info')
    country: Country = Field('de', title='Country', description='Decides which stations are popular')


class RadioDirectoriesSettings(BaseModel):
    radiobrowser: RadioBrowserSettings = Field(default_factory=RadioBrowserSettings, title='radio-browser.info')


class RadioDirectories(Plugin):
    """Search for radio stations in radio-browser.info."""

    name = 'radio_directories'
    title = 'Find radio stations'
    interface_version = '1.1'
    requires = {'radio': '>=3.0,<4'}
    settings = RadioDirectoriesSettings

    def __init__(self):
        self._registered: List[str] = []

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._register()

    def settings_changed(self, changed) -> bool:
        self._register()
        return True

    def _register(self) -> None:
        points = self._ctx.modules.radio.directories
        for key in self._registered:
            points.unregister(key)
        self._registered = []
        config = self._ctx.config
        if config.get('radiobrowser', 'enabled', default=True):
            points.register('radiobrowser', RadioBrowser('radio-browser.info',
                                                         country=config.get('radiobrowser', 'country', default='de')))
            self._registered.append('radiobrowser')
