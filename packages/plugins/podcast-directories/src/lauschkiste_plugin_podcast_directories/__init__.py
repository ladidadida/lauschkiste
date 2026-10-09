"""Find podcasts in directories and subscribe to them.

Every directory is an entry of ``directories``; it can be switched off (``enabled: false``) and its address
changed, and entries of the kind ``json`` describe any other directory that answers with JSON::

    plugins:
      podcast_directories:
        directories:
          fyyd: {kind: fyyd, enabled: false}
"""

import logging
from typing import Dict, List, Literal

from pydantic import BaseModel, Field

from lauschkiste.contract import Plugin
from lauschkiste_plugin_podcast_directories.directories import KINDS

logger = logging.getLogger('lauschkiste.podcast_directories')


class DirectorySettings(BaseModel):
    kind: Literal['itunes', 'fyyd', 'podcastindex', 'json'] = Field('itunes', title='Kind')
    enabled: bool = Field(True, title='On')
    label: str = Field('', title='Name', description='Shown with the results; empty: the entry name')
    url: str = Field('', title='Address', description='Empty: the usual address of this kind')
    country: str = Field('DE', title='Country (Apple)')
    language: str = Field('de', title='Language (fyyd, Podcast Index)')
    search_url: str = Field('', title='Search address (json)', description='With {term} and {limit}')
    top_url: str = Field('', title='Top list address (json)', description='With {limit}; empty: none')
    results: str = Field('', title='Path to the list (json)', description='e.g. data or feed.items; empty: the answer')
    title_key: str = Field('title', title='Field of the title (json)')
    feed_key: str = Field('feed_url', title='Field of the feed address (json)')
    author_key: str = Field('', title='Field of the author (json)')
    image_key: str = Field('', title='Field of the image (json)')


def default_directories() -> Dict[str, DirectorySettings]:
    return {'itunes': DirectorySettings(kind='itunes', label='Apple Podcasts'),
            'fyyd': DirectorySettings(kind='fyyd', label='fyyd'),
            'podcastindex': DirectorySettings(kind='podcastindex', label='Podcast Index', enabled=False)}


class PodcastDirectoriesSettings(BaseModel):
    directories: Dict[str, DirectorySettings] = Field(default_factory=default_directories, title='Directories')
    podcastindex_key: str = Field('', title='Podcast Index API key', json_schema_extra={'secret': True},
                                  description='podcastindex.org, free. Leave empty to keep the current one.')
    podcastindex_secret: str = Field('', title='Podcast Index API secret', json_schema_extra={'secret': True},
                                     description='Leave empty to keep the current one.')


class PodcastDirectories(Plugin):
    """Search for podcasts in Apple Podcasts, fyyd, the Podcast Index and directories of your own."""

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
        entries = config.get('directories', default=None)
        if not isinstance(entries, dict):
            entries = {key: value.model_dump() for key, value in default_directories().items()}
        for key, raw in entries.items():
            values = DirectorySettings(**{k: v for k, v in dict(raw or {}).items() if k in DirectorySettings.model_fields})
            if not values.enabled:
                continue
            options = values.model_dump(exclude={'kind', 'enabled', 'label'})
            options['key'] = lambda: config.get('podcastindex_key', default='')
            options['secret'] = lambda: config.get('podcastindex_secret', default='')
            points.register(key, KINDS[values.kind](label=values.label or key, **options))
            self._registered.append(key)
