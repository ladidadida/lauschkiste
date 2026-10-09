# Table of Contents

* [lauschkiste](#lauschkiste)
* [lauschkiste.utils](#lauschkiste.utils)
  * [get\_config\_action](#lauschkiste.utils.get_config_action)
  * [get\_git\_state](#lauschkiste.utils.get_git_state)
* [lauschkiste.jingle](#lauschkiste.jingle)
  * [sound\_path](#lauschkiste.jingle.sound_path)
  * [Jingle](#lauschkiste.jingle.Jingle)
    * [play](#lauschkiste.jingle.Jingle.play)
* [lauschkiste.library.index](#lauschkiste.library.index)
  * [read\_tags](#lauschkiste.library.index.read_tags)
  * [LibraryIndex](#lauschkiste.library.index.LibraryIndex)
    * [relative](#lauschkiste.library.index.LibraryIndex.relative)
    * [scan](#lauschkiste.library.index.LibraryIndex.scan)
    * [albums](#lauschkiste.library.index.LibraryIndex.albums)
* [lauschkiste.library.watch](#lauschkiste.library.watch)
  * [Snapshot](#lauschkiste.library.watch.Snapshot)
  * [snapshot](#lauschkiste.library.watch.snapshot)
  * [Inotify](#lauschkiste.library.watch.Inotify)
    * [wait](#lauschkiste.library.watch.Inotify.wait)
  * [FolderWatcher](#lauschkiste.library.watch.FolderWatcher)
* [lauschkiste.library.files](#lauschkiste.library.files)
  * [LibraryError](#lauschkiste.library.files.LibraryError)
  * [resolve\_library\_path](#lauschkiste.library.files.resolve_library_path)
  * [UploadSession](#lauschkiste.library.files.UploadSession)
  * [MusicLibrary](#lauschkiste.library.files.MusicLibrary)
* [lauschkiste.library.module](#lauschkiste.library.module)
  * [LibrarySource](#lauschkiste.library.module.LibrarySource)
    * [describe](#lauschkiste.library.module.LibrarySource.describe)
    * [list\_items](#lauschkiste.library.module.LibrarySource.list_items)
    * [cover](#lauschkiste.library.module.LibrarySource.cover)
  * [song\_from\_source](#lauschkiste.library.module.song_from_source)
  * [Library](#lauschkiste.library.module.Library)
    * [list\_entries](#lauschkiste.library.module.Library.list_entries)
    * [create\_folder](#lauschkiste.library.module.Library.create_folder)
    * [delete\_entries](#lauschkiste.library.module.Library.delete_entries)
    * [refresh](#lauschkiste.library.module.Library.refresh)
    * [list\_sources](#lauschkiste.library.module.Library.list_sources)
    * [list\_items](#lauschkiste.library.module.Library.list_items)
    * [list\_songs](#lauschkiste.library.module.Library.list_songs)
    * [list\_folder\_songs](#lauschkiste.library.module.Library.list_folder_songs)
    * [get\_song](#lauschkiste.library.module.Library.get_song)
    * [search](#lauschkiste.library.module.Library.search)
    * [get\_song\_cover](#lauschkiste.library.module.Library.get_song_cover)
    * [get\_album\_cover](#lauschkiste.library.module.Library.get_album_cover)
    * [flush\_covers](#lauschkiste.library.module.Library.flush_covers)
* [lauschkiste.library.covers](#lauschkiste.library.covers)
  * [CoverCache](#lauschkiste.library.covers.CoverCache)
    * [cover\_for](#lauschkiste.library.covers.CoverCache.cover_for)
* [lauschkiste.library](#lauschkiste.library)
  * [root](#lauschkiste.library.root)
* [lauschkiste.podcasts](#lauschkiste.podcasts)
  * [Podcast](#lauschkiste.podcasts.Podcast)
    * [hidden](#lauschkiste.podcasts.Podcast.hidden)
  * [Episode](#lauschkiste.podcasts.Episode)
    * [item](#lauschkiste.podcasts.Episode.item)
    * [availability](#lauschkiste.podcasts.Episode.availability)
  * [PodcastHit](#lauschkiste.podcasts.PodcastHit)
  * [SearchResult](#lauschkiste.podcasts.SearchResult)
    * [errors](#lauschkiste.podcasts.SearchResult.errors)
  * [PodcastDirectory](#lauschkiste.podcasts.PodcastDirectory)
    * [search](#lauschkiste.podcasts.PodcastDirectory.search)
    * [top](#lauschkiste.podcasts.PodcastDirectory.top)
  * [EpisodeProvider](#lauschkiste.podcasts.EpisodeProvider)
  * [parse\_feed](#lauschkiste.podcasts.parse_feed)
  * [Podcasts](#lauschkiste.podcasts.Podcasts)
    * [list\_podcasts](#lauschkiste.podcasts.Podcasts.list_podcasts)
    * [list\_episodes](#lauschkiste.podcasts.Podcasts.list_episodes)
    * [add\_podcast](#lauschkiste.podcasts.Podcasts.add_podcast)
    * [update\_podcast](#lauschkiste.podcasts.Podcasts.update_podcast)
    * [delete\_podcast](#lauschkiste.podcasts.Podcasts.delete_podcast)
    * [refresh](#lauschkiste.podcasts.Podcasts.refresh)
    * [list\_directories](#lauschkiste.podcasts.Podcasts.list_directories)
    * [search](#lauschkiste.podcasts.Podcasts.search)
    * [top](#lauschkiste.podcasts.Podcasts.top)
    * [import\_opml](#lauschkiste.podcasts.Podcasts.import_opml)
    * [export\_opml](#lauschkiste.podcasts.Podcasts.export_opml)
    * [hide\_from\_continue](#lauschkiste.podcasts.Podcasts.hide_from_continue)
    * [play](#lauschkiste.podcasts.Podcasts.play)
    * [set\_heard](#lauschkiste.podcasts.Podcasts.set_heard)
* [lauschkiste.directories](#lauschkiste.directories)
  * [ask](#lauschkiste.directories.ask)
  * [interleave](#lauschkiste.directories.interleave)
* [lauschkiste.radio\_playlist](#lauschkiste.radio_playlist)
  * [parse\_stations](#lauschkiste.radio_playlist.parse_stations)
  * [render\_m3u](#lauschkiste.radio_playlist.render_m3u)
* [lauschkiste.rfid.reader](#lauschkiste.rfid.reader)
  * [ReaderDriver](#lauschkiste.rfid.reader.ReaderDriver)
    * [create\_reader](#lauschkiste.rfid.reader.ReaderDriver.create_reader)
  * [ReaderSetting](#lauschkiste.rfid.reader.ReaderSetting)
  * [CardDetected](#lauschkiste.rfid.reader.CardDetected)
    * [learned](#lauschkiste.rfid.reader.CardDetected.learned)
  * [CardRemovalTimer](#lauschkiste.rfid.reader.CardRemovalTimer)
  * [Rfid](#lauschkiste.rfid.reader.Rfid)
    * [claims](#lauschkiste.rfid.reader.Rfid.claims)
    * [resolve\_config\_action](#lauschkiste.rfid.reader.Rfid.resolve_config_action)
    * [learn](#lauschkiste.rfid.reader.Rfid.learn)
    * [stop\_learning](#lauschkiste.rfid.reader.Rfid.stop_learning)
    * [list\_readers](#lauschkiste.rfid.reader.Rfid.list_readers)
* [lauschkiste.rfid.readerbase](#lauschkiste.rfid.readerbase)
  * [ReaderBaseClass](#lauschkiste.rfid.readerbase.ReaderBaseClass)
* [lauschkiste.rfid](#lauschkiste.rfid)
* [lauschkiste.rfid.cards](#lauschkiste.rfid.cards)
  * [Cards](#lauschkiste.rfid.cards.Cards)
    * [list\_cards](#lauschkiste.rfid.cards.Cards.list_cards)
    * [get\_card](#lauschkiste.rfid.cards.Cards.get_card)
    * [register\_card](#lauschkiste.rfid.cards.Cards.register_card)
    * [delete\_card](#lauschkiste.rfid.cards.Cards.delete_card)
* [lauschkiste.rfid.cardutils](#lauschkiste.rfid.cardutils)
  * [card\_command\_to\_str](#lauschkiste.rfid.cardutils.card_command_to_str)
* [lauschkiste.audiobooks](#lauschkiste.audiobooks)
  * [AudiobookSource](#lauschkiste.audiobooks.AudiobookSource)
    * [list\_books](#lauschkiste.audiobooks.AudiobookSource.list_books)
    * [files](#lauschkiste.audiobooks.AudiobookSource.files)
    * [title](#lauschkiste.audiobooks.AudiobookSource.title)
    * [position](#lauschkiste.audiobooks.AudiobookSource.position)
    * [set\_finished](#lauschkiste.audiobooks.AudiobookSource.set_finished)
  * [Audiobook](#lauschkiste.audiobooks.Audiobook)
    * [availability](#lauschkiste.audiobooks.Audiobook.availability)
    * [hidden](#lauschkiste.audiobooks.Audiobook.hidden)
  * [Audiobooks](#lauschkiste.audiobooks.Audiobooks)
    * [list\_books](#lauschkiste.audiobooks.Audiobooks.list_books)
    * [play](#lauschkiste.audiobooks.Audiobooks.play)
    * [hide\_from\_continue](#lauschkiste.audiobooks.Audiobooks.hide_from_continue)
    * [restart](#lauschkiste.audiobooks.Audiobooks.restart)
    * [set\_finished](#lauschkiste.audiobooks.Audiobooks.set_finished)
* [lauschkiste.volume](#lauschkiste.volume)
  * [PlayerMixer](#lauschkiste.volume.PlayerMixer)
  * [PulseMixer](#lauschkiste.volume.PulseMixer)
  * [pulse\_sinks](#lauschkiste.volume.pulse_sinks)
  * [Volume](#lauschkiste.volume.Volume)
    * [get\_volume](#lauschkiste.volume.Volume.get_volume)
    * [set\_volume](#lauschkiste.volume.Volume.set_volume)
    * [change\_volume](#lauschkiste.volume.Volume.change_volume)
    * [mute](#lauschkiste.volume.Volume.mute)
    * [list\_sinks](#lauschkiste.volume.Volume.list_sinks)
    * [set\_soft\_max\_volume](#lauschkiste.volume.Volume.set_soft_max_volume)
    * [get\_outputs](#lauschkiste.volume.Volume.get_outputs)
    * [set\_output](#lauschkiste.volume.Volume.set_output)
    * [toggle\_output](#lauschkiste.volume.Volume.toggle_output)
    * [fade\_out](#lauschkiste.volume.Volume.fade_out)
* [lauschkiste.startup](#lauschkiste.startup)
  * [import\_fastapi](#lauschkiste.startup.import_fastapi)
* [lauschkiste.nv\_manager](#lauschkiste.nv_manager)
* [lauschkiste.dismissed](#lauschkiste.dismissed)
  * [Dismissed](#lauschkiste.dismissed.Dismissed)
* [lauschkiste.radio](#lauschkiste.radio)
  * [Station](#lauschkiste.radio.Station)
    * [last\_played](#lauschkiste.radio.Station.last_played)
  * [StationHit](#lauschkiste.radio.StationHit)
    * [added](#lauschkiste.radio.StationHit.added)
  * [SearchResult](#lauschkiste.radio.SearchResult)
    * [errors](#lauschkiste.radio.SearchResult.errors)
  * [RadioDirectory](#lauschkiste.radio.RadioDirectory)
    * [search](#lauschkiste.radio.RadioDirectory.search)
    * [top](#lauschkiste.radio.RadioDirectory.top)
  * [streams\_in\_playlist](#lauschkiste.radio.streams_in_playlist)
  * [Radio](#lauschkiste.radio.Radio)
    * [list\_stations](#lauschkiste.radio.Radio.list_stations)
    * [add\_station](#lauschkiste.radio.Radio.add_station)
    * [update\_station](#lauschkiste.radio.Radio.update_station)
    * [delete\_station](#lauschkiste.radio.Radio.delete_station)
    * [list\_directories](#lauschkiste.radio.Radio.list_directories)
    * [search](#lauschkiste.radio.Radio.search)
    * [top](#lauschkiste.radio.Radio.top)
    * [import\_playlist](#lauschkiste.radio.Radio.import_playlist)
    * [export\_playlist](#lauschkiste.radio.Radio.export_playlist)
    * [play](#lauschkiste.radio.Radio.play)
    * [forget\_recent](#lauschkiste.radio.Radio.forget_recent)
* [lauschkiste.publishing.bus](#lauschkiste.publishing.bus)
  * [EventBus](#lauschkiste.publishing.bus.EventBus)
    * [publish](#lauschkiste.publishing.bus.EventBus.publish)
    * [resend](#lauschkiste.publishing.bus.EventBus.resend)
    * [cache\_snapshot](#lauschkiste.publishing.bus.EventBus.cache_snapshot)
* [lauschkiste.publishing](#lauschkiste.publishing)
  * [get\_bus](#lauschkiste.publishing.get_bus)
* [lauschkiste.cache.worker](#lauschkiste.cache.worker)
  * [Download](#lauschkiste.cache.worker.Download)
    * [fetch](#lauschkiste.cache.worker.Download.fetch)
* [lauschkiste.cache.manager](#lauschkiste.cache.manager)
* [lauschkiste.cache](#lauschkiste.cache)
  * [CacheFile](#lauschkiste.cache.CacheFile)
    * [size](#lauschkiste.cache.CacheFile.size)
  * [CacheProvider](#lauschkiste.cache.CacheProvider)
    * [plan](#lauschkiste.cache.CacheProvider.plan)
    * [version](#lauschkiste.cache.CacheProvider.version)
    * [removable](#lauschkiste.cache.CacheProvider.removable)
  * [Cache](#lauschkiste.cache.Cache)
    * [downloads](#lauschkiste.cache.Cache.downloads)
    * [files](#lauschkiste.cache.Cache.files)
    * [cached](#lauschkiste.cache.Cache.cached)
    * [download](#lauschkiste.cache.Cache.download)
    * [cancel](#lauschkiste.cache.Cache.cancel)
    * [remove](#lauschkiste.cache.Cache.remove)
* [lauschkiste.cache.store](#lauschkiste.cache.store)
  * [INTERNAL](#lauschkiste.cache.store.INTERNAL)
  * [CacheStore](#lauschkiste.cache.store.CacheStore)
    * [complete](#lauschkiste.cache.store.CacheStore.complete)
    * [items](#lauschkiste.cache.store.CacheStore.items)
    * [set\_rate](#lauschkiste.cache.store.CacheStore.set_rate)
* [lauschkiste.playlistgenerator](#lauschkiste.playlistgenerator)
  * [TYPE\_DECODE](#lauschkiste.playlistgenerator.TYPE_DECODE)
  * [PlaylistCollector](#lauschkiste.playlistgenerator.PlaylistCollector)
    * [\_\_init\_\_](#lauschkiste.playlistgenerator.PlaylistCollector.__init__)
    * [set\_exclusion\_endings](#lauschkiste.playlistgenerator.PlaylistCollector.set_exclusion_endings)
    * [get\_directory\_content](#lauschkiste.playlistgenerator.PlaylistCollector.get_directory_content)
    * [parse](#lauschkiste.playlistgenerator.PlaylistCollector.parse)
* [lauschkiste.api.events](#lauschkiste.api.events)
  * [EventBroker](#lauschkiste.api.events.EventBroker)
    * [publish](#lauschkiste.api.events.EventBroker.publish)
  * [parse\_subscription\_command](#lauschkiste.api.events.parse_subscription_command)
* [lauschkiste.api](#lauschkiste.api)
* [lauschkiste.api.fastapi\_server](#lauschkiste.api.fastapi_server)
  * [default\_webapp\_build\_dir](#lauschkiste.api.fastapi_server.default_webapp_build_dir)
  * [BodySizeLimit](#lauschkiste.api.fastapi_server.BodySizeLimit)
  * [FastApiServer](#lauschkiste.api.fastapi_server.FastApiServer)
    * [start\_and\_wait](#lauschkiste.api.fastapi_server.FastApiServer.start_and_wait)
* [lauschkiste.api.webapp\_static](#lauschkiste.api.webapp_static)
  * [HASHED\_ASSETS\_DIR](#lauschkiste.api.webapp_static.HASHED_ASSETS_DIR)
  * [CACHE\_NEVER](#lauschkiste.api.webapp_static.CACHE_NEVER)
  * [register\_webapp\_routes](#lauschkiste.api.webapp_static.register_webapp_routes)
* [lauschkiste.version](#lauschkiste.version)
  * [version](#lauschkiste.version.version)
  * [version\_info](#lauschkiste.version.version_info)
* [lauschkiste.podcast\_opml](#lauschkiste.podcast_opml)
  * [normalize\_url](#lauschkiste.podcast_opml.normalize_url)
  * [parse\_opml](#lauschkiste.podcast_opml.parse_opml)
  * [render\_opml](#lauschkiste.podcast_opml.render_opml)
* [lauschkiste.cfghandler](#lauschkiste.cfghandler)
  * [ConfigHandler](#lauschkiste.cfghandler.ConfigHandler)
    * [loaded\_from](#lauschkiste.cfghandler.ConfigHandler.loaded_from)
    * [get](#lauschkiste.cfghandler.ConfigHandler.get)
    * [setdefault](#lauschkiste.cfghandler.ConfigHandler.setdefault)
    * [getn](#lauschkiste.cfghandler.ConfigHandler.getn)
    * [setn](#lauschkiste.cfghandler.ConfigHandler.setn)
    * [setndefault](#lauschkiste.cfghandler.ConfigHandler.setndefault)
    * [config\_dict](#lauschkiste.cfghandler.ConfigHandler.config_dict)
    * [is\_modified](#lauschkiste.cfghandler.ConfigHandler.is_modified)
    * [clear\_modified](#lauschkiste.cfghandler.ConfigHandler.clear_modified)
    * [save](#lauschkiste.cfghandler.ConfigHandler.save)
    * [load](#lauschkiste.cfghandler.ConfigHandler.load)
  * [get\_handler](#lauschkiste.cfghandler.get_handler)
  * [load\_yaml](#lauschkiste.cfghandler.load_yaml)
  * [ensure\_default\_config](#lauschkiste.cfghandler.ensure_default_config)
  * [write\_yaml](#lauschkiste.cfghandler.write_yaml)
* [lauschkiste.timers](#lauschkiste.timers)
  * [Timers](#lauschkiste.timers.Timers)
    * [list\_timers](#lauschkiste.timers.Timers.list_timers)
    * [start\_timer](#lauschkiste.timers.Timers.start_timer)
    * [cancel](#lauschkiste.timers.Timers.cancel)
    * [toggle](#lauschkiste.timers.Timers.toggle)
* [lauschkiste.audio\_output](#lauschkiste.audio_output)
  * [volume\_gain](#lauschkiste.audio_output.volume_gain)
  * [scale\_gain](#lauschkiste.audio_output.scale_gain)
  * [scale\_volume](#lauschkiste.audio_output.scale_volume)
  * [AudioSink](#lauschkiste.audio_output.AudioSink)
    * [close](#lauschkiste.audio_output.AudioSink.close)
  * [PortAudioSink](#lauschkiste.audio_output.PortAudioSink)
    * [LATENCY](#lauschkiste.audio_output.PortAudioSink.LATENCY)
    * [CHUNK\_SECONDS](#lauschkiste.audio_output.PortAudioSink.CHUNK_SECONDS)
    * [LEAD\_IN\_SECONDS](#lauschkiste.audio_output.PortAudioSink.LEAD_IN_SECONDS)
  * [play\_file](#lauschkiste.audio_output.play_file)
* [lauschkiste.core\_modules](#lauschkiste.core_modules)
* [lauschkiste.statefile](#lauschkiste.statefile)
  * [write\_text](#lauschkiste.statefile.write_text)
* [lauschkiste.input\_devices](#lauschkiste.input_devices)
  * [Evdev](#lauschkiste.input_devices.Evdev)
    * [key\_downs](#lauschkiste.input_devices.Evdev.key_downs)
  * [InputDevices](#lauschkiste.input_devices.InputDevices)
    * [available\_devices](#lauschkiste.input_devices.InputDevices.available_devices)
    * [list\_devices](#lauschkiste.input_devices.InputDevices.list_devices)
* [lauschkiste.multitimer](#lauschkiste.multitimer)
  * [MultiTimer](#lauschkiste.multitimer.MultiTimer)
    * [cancel](#lauschkiste.multitimer.MultiTimer.cancel)
    * [trigger](#lauschkiste.multitimer.MultiTimer.trigger)
    * [run](#lauschkiste.multitimer.MultiTimer.run)
  * [GenericTimerClass](#lauschkiste.multitimer.GenericTimerClass)
    * [start](#lauschkiste.multitimer.GenericTimerClass.start)
    * [cancel](#lauschkiste.multitimer.GenericTimerClass.cancel)
    * [cancel\_generation](#lauschkiste.multitimer.GenericTimerClass.cancel_generation)
    * [toggle](#lauschkiste.multitimer.GenericTimerClass.toggle)
    * [trigger](#lauschkiste.multitimer.GenericTimerClass.trigger)
    * [is\_alive](#lauschkiste.multitimer.GenericTimerClass.is_alive)
    * [get\_timeout](#lauschkiste.multitimer.GenericTimerClass.get_timeout)
    * [set\_timeout](#lauschkiste.multitimer.GenericTimerClass.set_timeout)
    * [publish](#lauschkiste.multitimer.GenericTimerClass.publish)
    * [get\_state](#lauschkiste.multitimer.GenericTimerClass.get_state)
    * [close](#lauschkiste.multitimer.GenericTimerClass.close)
  * [GenericEndlessTimerClass](#lauschkiste.multitimer.GenericEndlessTimerClass)
    * [get\_state](#lauschkiste.multitimer.GenericEndlessTimerClass.get_state)
* [lauschkiste.paths](#lauschkiste.paths)
  * [home](#lauschkiste.paths.home)
  * [set\_home](#lauschkiste.paths.set_home)
  * [resolve](#lauschkiste.paths.resolve)
  * [library\_dir](#lauschkiste.paths.library_dir)
  * [resource](#lauschkiste.paths.resource)
* [lauschkiste.daemon](#lauschkiste.daemon)
  * [DEFAULT\_CONFIG\_TEMPLATE](#lauschkiste.daemon.DEFAULT_CONFIG_TEMPLATE)
  * [shutdown\_signal](#lauschkiste.daemon.shutdown_signal)
  * [log\_active\_threads](#lauschkiste.daemon.log_active_threads)
  * [Daemon](#lauschkiste.daemon.Daemon)
    * [signal\_handler](#lauschkiste.daemon.Daemon.signal_handler)
* [lauschkiste.misc.simplecolors](#lauschkiste.misc.simplecolors)
  * [Colors](#lauschkiste.misc.simplecolors.Colors)
  * [resolve](#lauschkiste.misc.simplecolors.resolve)
  * [print](#lauschkiste.misc.simplecolors.print)
* [lauschkiste.misc](#lauschkiste.misc)
  * [recursive\_chmod](#lauschkiste.misc.recursive_chmod)
  * [flatten](#lauschkiste.misc.flatten)
  * [getattr\_hierarchical](#lauschkiste.misc.getattr_hierarchical)
* [lauschkiste.misc.inputminus](#lauschkiste.misc.inputminus)
  * [input\_int](#lauschkiste.misc.inputminus.input_int)
  * [input\_yesno](#lauschkiste.misc.inputminus.input_yesno)
* [lauschkiste.misc.loggingext](#lauschkiste.misc.loggingext)
  * [ColorFilter](#lauschkiste.misc.loggingext.ColorFilter)
    * [\_\_init\_\_](#lauschkiste.misc.loggingext.ColorFilter.__init__)
  * [PubStream](#lauschkiste.misc.loggingext.PubStream)
  * [PubStreamHandler](#lauschkiste.misc.loggingext.PubStreamHandler)
* [lauschkiste.time\_limits](#lauschkiste.time_limits)
  * [SETTLE\_SEC](#lauschkiste.time_limits.SETTLE_SEC)
  * [TimeLimitStatus](#lauschkiste.time_limits.TimeLimitStatus)
    * [enabled](#lauschkiste.time_limits.TimeLimitStatus.enabled)
    * [clock\_ok](#lauschkiste.time_limits.TimeLimitStatus.clock_ok)
    * [reason](#lauschkiste.time_limits.TimeLimitStatus.reason)
    * [until](#lauschkiste.time_limits.TimeLimitStatus.until)
  * [clock\_synchronized](#lauschkiste.time_limits.clock_synchronized)
  * [TimeLimits](#lauschkiste.time_limits.TimeLimits)
    * [evaluate](#lauschkiste.time_limits.TimeLimits.evaluate)
    * [status](#lauschkiste.time_limits.TimeLimits.status)
    * [allow](#lauschkiste.time_limits.TimeLimits.allow)
    * [reset\_today](#lauschkiste.time_limits.TimeLimits.reset_today)
* [lauschkiste.time\_limits.rules](#lauschkiste.time_limits.rules)
  * [quiet\_until](#lauschkiste.time_limits.rules.quiet_until)
  * [limit\_seconds](#lauschkiste.time_limits.rules.limit_seconds)
* [lauschkiste.contract.secrets](#lauschkiste.contract.secrets)
  * [SecretStore](#lauschkiste.contract.secrets.SecretStore)
    * [set](#lauschkiste.contract.secrets.SecretStore.set)
* [lauschkiste.contract.interfaces](#lauschkiste.contract.interfaces)
  * [format\_signature](#lauschkiste.contract.interfaces.format_signature)
* [lauschkiste.contract.declarations](#lauschkiste.contract.declarations)
  * [OperationSpec](#lauschkiste.contract.declarations.OperationSpec)
    * [kind](#lauschkiste.contract.declarations.OperationSpec.kind)
  * [action](#lauschkiste.contract.declarations.action)
  * [query](#lauschkiste.contract.declarations.query)
  * [EventSpec](#lauschkiste.contract.declarations.EventSpec)
  * [ExtensionPoint](#lauschkiste.contract.declarations.ExtensionPoint)
    * [on\_register](#lauschkiste.contract.declarations.ExtensionPoint.on_register)
  * [ExtensionPointSpec](#lauschkiste.contract.declarations.ExtensionPointSpec)
  * [Operation](#lauschkiste.contract.declarations.Operation)
    * [validate\_args](#lauschkiste.contract.declarations.Operation.validate_args)
* [lauschkiste.contract.catalog](#lauschkiste.contract.catalog)
  * [ActionCatalog](#lauschkiste.contract.catalog.ActionCatalog)
    * [validate](#lauschkiste.contract.catalog.ActionCatalog.validate)
    * [bind](#lauschkiste.contract.catalog.ActionCatalog.bind)
* [lauschkiste.contract.context](#lauschkiste.contract.context)
  * [ModuleConfig](#lauschkiste.contract.context.ModuleConfig)
  * [ModuleProxy](#lauschkiste.contract.context.ModuleProxy)
  * [Context](#lauschkiste.contract.context.Context)
    * [lock](#lauschkiste.contract.context.Context.lock)
    * [subscribe](#lauschkiste.contract.context.Context.subscribe)
* [lauschkiste.contract.routes](#lauschkiste.contract.routes)
  * [response\_adapter](#lauschkiste.contract.routes.response_adapter)
  * [add\_response\_schemas](#lauschkiste.contract.routes.add_response_schemas)
  * [add\_settings\_routes](#lauschkiste.contract.routes.add_settings_routes)
  * [add\_plugin\_routes](#lauschkiste.contract.routes.add_plugin_routes)
* [lauschkiste.contract.manager](#lauschkiste.contract.manager)
  * [discover\_plugins](#lauschkiste.contract.manager.discover_plugins)
  * [ModuleHandle](#lauschkiste.contract.manager.ModuleHandle)
  * [ModuleManager](#lauschkiste.contract.manager.ModuleManager)
    * [\_\_init\_\_](#lauschkiste.contract.manager.ModuleManager.__init__)
* [lauschkiste.contract.module](#lauschkiste.contract.module)
  * [Module](#lauschkiste.contract.module.Module)
    * [concurrency](#lauschkiste.contract.module.Module.concurrency)
    * [settings](#lauschkiste.contract.module.Module.settings)
    * [ready](#lauschkiste.contract.module.Module.ready)
    * [settings\_changed](#lauschkiste.contract.module.Module.settings_changed)
    * [extra\_routes](#lauschkiste.contract.module.Module.extra_routes)
  * [CoreModule](#lauschkiste.contract.module.CoreModule)
  * [Plugin](#lauschkiste.contract.module.Plugin)
    * [extras](#lauschkiste.contract.module.Plugin.extras)
    * [title](#lauschkiste.contract.module.Plugin.title)
    * [provides](#lauschkiste.contract.module.Plugin.provides)
    * [needs](#lauschkiste.contract.module.Plugin.needs)
    * [detect](#lauschkiste.contract.module.Plugin.detect)
* [lauschkiste.contract.version](#lauschkiste.contract.version)
  * [CONTRACT\_VERSION](#lauschkiste.contract.version.CONTRACT_VERSION)
* [lauschkiste.contract](#lauschkiste.contract)
* [lauschkiste.contract.snapshots](#lauschkiste.contract.snapshots)
  * [check\_target](#lauschkiste.contract.snapshots.check_target)
* [lauschkiste.contract.settings](#lauschkiste.contract.settings)
  * [ActionEntry](#lauschkiste.contract.settings.ActionEntry)
  * [storage](#lauschkiste.contract.settings.storage)
  * [secret\_fields](#lauschkiste.contract.settings.secret_fields)
  * [current\_values](#lauschkiste.contract.settings.current_values)
  * [SettingsStore](#lauschkiste.contract.settings.SettingsStore)
* [lauschkiste.contract.errors](#lauschkiste.contract.errors)
  * [ContractError](#lauschkiste.contract.errors.ContractError)
  * [OperationError](#lauschkiste.contract.errors.OperationError)
  * [ActionError](#lauschkiste.contract.errors.ActionError)
* [lauschkiste.contract.plugins](#lauschkiste.contract.plugins)
  * [readable](#lauschkiste.contract.plugins.readable)
  * [package\_info](#lauschkiste.contract.plugins.package_info)
  * [installed](#lauschkiste.contract.plugins.installed)
  * [load](#lauschkiste.contract.plugins.load)
  * [taken\_by](#lauschkiste.contract.plugins.taken_by)
  * [missing\_needs](#lauschkiste.contract.plugins.missing_needs)
  * [blocker](#lauschkiste.contract.plugins.blocker)
  * [why\_not\_enable](#lauschkiste.contract.plugins.why_not_enable)
  * [detected\_boards](#lauschkiste.contract.plugins.detected_boards)
  * [plugin\_extras](#lauschkiste.contract.plugins.plugin_extras)
  * [missing\_extras](#lauschkiste.contract.plugins.missing_extras)
  * [install\_command](#lauschkiste.contract.plugins.install_command)
  * [ExtrasInstaller](#lauschkiste.contract.plugins.ExtrasInstaller)
    * [start](#lauschkiste.contract.plugins.ExtrasInstaller.start)
  * [set\_enabled](#lauschkiste.contract.plugins.set_enabled)
  * [describe](#lauschkiste.contract.plugins.describe)
  * [translations](#lauschkiste.contract.plugins.translations)
* [lauschkiste.system](#lauschkiste.system)
  * [cpu\_temperature](#lauschkiste.system.cpu_temperature)
  * [ip\_addresses](#lauschkiste.system.ip_addresses)
  * [own\_unit](#lauschkiste.system.own_unit)
  * [System](#lauschkiste.system.System)
    * [log](#lauschkiste.system.System.log)
    * [get\_info](#lauschkiste.system.System.get_info)
    * [get\_health](#lauschkiste.system.System.get_health)
    * [get\_ip\_addresses](#lauschkiste.system.System.get_ip_addresses)
    * [say\_my\_ip](#lauschkiste.system.System.say_my_ip)
    * [restart\_service](#lauschkiste.system.System.restart_service)
    * [get\_log](#lauschkiste.system.System.get_log)
    * [get\_app\_settings](#lauschkiste.system.System.get_app_settings)
    * [set\_app\_settings](#lauschkiste.system.System.set_app_settings)
    * [noop](#lauschkiste.system.System.noop)
* [lauschkiste.hardware](#lauschkiste.hardware)
  * [Claim](#lauschkiste.hardware.Claim)
  * [Board](#lauschkiste.hardware.Board)
    * [describe](#lauschkiste.hardware.Board.describe)
    * [pin\_id](#lauschkiste.hardware.Board.pin_id)
    * [gpio\_line](#lauschkiste.hardware.Board.gpio_line)
    * [boot\_pending](#lauschkiste.hardware.Board.boot_pending)
  * [Hardware](#lauschkiste.hardware.Hardware)
    * [get\_state](#lauschkiste.hardware.Hardware.get_state)
    * [pin\_options](#lauschkiste.hardware.Hardware.pin_options)
    * [gpio\_line](#lauschkiste.hardware.Hardware.gpio_line)
    * [shutdown](#lauschkiste.hardware.Hardware.shutdown)
    * [reboot](#lauschkiste.hardware.Hardware.reboot)
* [lauschkiste.resume](#lauschkiste.resume)
  * [relative](#lauschkiste.resume.relative)
  * [PositionStore](#lauschkiste.resume.PositionStore)
  * [ResumeTracker](#lauschkiste.resume.ResumeTracker)
    * [set\_finished](#lauschkiste.resume.ResumeTracker.set_finished)
    * [play](#lauschkiste.resume.ResumeTracker.play)
* [lauschkiste.player.coordinator](#lauschkiste.player.coordinator)
  * [PlayerCoordinator](#lauschkiste.player.coordinator.PlayerCoordinator)
    * [\_\_init\_\_](#lauschkiste.player.coordinator.PlayerCoordinator.__init__)
    * [register\_backend](#lauschkiste.player.coordinator.PlayerCoordinator.register_backend)
    * [set\_default\_backend](#lauschkiste.player.coordinator.PlayerCoordinator.set_default_backend)
    * [select\_backend](#lauschkiste.player.coordinator.PlayerCoordinator.select_backend)
    * [set\_speed](#lauschkiste.player.coordinator.PlayerCoordinator.set_speed)
    * [play\_files](#lauschkiste.player.coordinator.PlayerCoordinator.play_files)
* [lauschkiste.player.module](#lauschkiste.player.module)
  * [Player](#lauschkiste.player.module.Player)
    * [play](#lauschkiste.player.module.Player.play)
    * [pause](#lauschkiste.player.module.Player.pause)
    * [toggle](#lauschkiste.player.module.Player.toggle)
    * [next](#lauschkiste.player.module.Player.next)
    * [prev](#lauschkiste.player.module.Player.prev)
    * [stop\_playback](#lauschkiste.player.module.Player.stop_playback)
    * [seek](#lauschkiste.player.module.Player.seek)
    * [shuffle](#lauschkiste.player.module.Player.shuffle)
    * [repeat](#lauschkiste.player.module.Player.repeat)
    * [jump](#lauschkiste.player.module.Player.jump)
    * [set\_speed](#lauschkiste.player.module.Player.set_speed)
    * [get\_queue](#lauschkiste.player.module.Player.get_queue)
    * [stop\_after\_current](#lauschkiste.player.module.Player.stop_after_current)
    * [rewind](#lauschkiste.player.module.Player.rewind)
    * [replay](#lauschkiste.player.module.Player.replay)
    * [replay\_if\_stopped](#lauschkiste.player.module.Player.replay_if_stopped)
    * [resume](#lauschkiste.player.module.Player.resume)
    * [play\_folder](#lauschkiste.player.module.Player.play_folder)
    * [play\_card](#lauschkiste.player.module.Player.play_card)
    * [play\_single](#lauschkiste.player.module.Player.play_single)
    * [play\_album](#lauschkiste.player.module.Player.play_album)
    * [play\_files](#lauschkiste.player.module.Player.play_files)
    * [queue\_load](#lauschkiste.player.module.Player.queue_load)
    * [update](#lauschkiste.player.module.Player.update)
    * [update\_wait](#lauschkiste.player.module.Player.update_wait)
    * [playerstatus](#lauschkiste.player.module.Player.playerstatus)
    * [get\_volume](#lauschkiste.player.module.Player.get_volume)
    * [set\_volume](#lauschkiste.player.module.Player.set_volume)
    * [playlistinfo](#lauschkiste.player.module.Player.playlistinfo)
    * [get\_current\_song](#lauschkiste.player.module.Player.get_current_song)
    * [get\_player\_type\_and\_version](#lauschkiste.player.module.Player.get_player_type_and_version)
    * [list\_backends](#lauschkiste.player.module.Player.list_backends)
    * [get\_active\_backend](#lauschkiste.player.module.Player.get_active_backend)
    * [get\_default\_backend](#lauschkiste.player.module.Player.get_default_backend)
    * [select\_backend](#lauschkiste.player.module.Player.select_backend)
* [lauschkiste.player.status](#lauschkiste.player.status)
  * [PlaybackContext](#lauschkiste.player.status.PlaybackContext)
    * [image](#lauschkiste.player.status.PlaybackContext.image)
  * [PlayerStatus](#lauschkiste.player.status.PlayerStatus)
    * [name](#lauschkiste.player.status.PlayerStatus.name)
    * [genre](#lauschkiste.player.status.PlayerStatus.genre)
  * [status\_from\_backend](#lauschkiste.player.status.status_from_backend)
* [lauschkiste.player](#lauschkiste.player)
* [lauschkiste.player.backend](#lauschkiste.player.backend)
  * [PlayerBackend](#lauschkiste.player.backend.PlayerBackend)
    * [set\_status\_callback](#lauschkiste.player.backend.PlayerBackend.set_status_callback)
    * [jump](#lauschkiste.player.backend.PlayerBackend.jump)
    * [stop\_after\_current](#lauschkiste.player.backend.PlayerBackend.stop_after_current)
    * [play\_files](#lauschkiste.player.backend.PlayerBackend.play_files)
  * [LevelMeter](#lauschkiste.player.backend.LevelMeter)
    * [level](#lauschkiste.player.backend.LevelMeter.level)
  * [Resolver](#lauschkiste.player.backend.Resolver)
    * [resolve](#lauschkiste.player.backend.Resolver.resolve)
* [lauschkiste.player.backends.local\_audio](#lauschkiste.player.backends.local_audio)
  * [ca\_file](#lauschkiste.player.backends.local_audio.ca_file)
  * [PlayerLocalAudio](#lauschkiste.player.backends.local_audio.PlayerLocalAudio)
    * [set\_level\_callback](#lauschkiste.player.backends.local_audio.PlayerLocalAudio.set_level_callback)
    * [rewind](#lauschkiste.player.backends.local_audio.PlayerLocalAudio.rewind)
    * [replay](#lauschkiste.player.backends.local_audio.PlayerLocalAudio.replay)
* [lauschkiste.player.backends](#lauschkiste.player.backends)

<a id="lauschkiste"></a>

# lauschkiste

<a id="lauschkiste.utils"></a>

# lauschkiste.utils

Common utility functions


<a id="lauschkiste.utils.get_config_action"></a>

#### get\_config\_action

```python
def get_config_action(cfg, section, option, default, valid_actions_dict,
                      logger)
```

Looks up the given {section}.{option} config option and returns

the associated entry from valid_actions_dict, if valid. Falls back to the given
default otherwise.


<a id="lauschkiste.utils.get_git_state"></a>

#### get\_git\_state

```python
def get_git_state()
```

Git state of the checkout Lauschkiste runs from, or a note that it isn't one (package install).


<a id="lauschkiste.jingle"></a>

# lauschkiste.jingle

The jingle core module: startup and shutdown sounds, and playing a sound on demand.


<a id="lauschkiste.jingle.sound_path"></a>

#### sound\_path

```python
def sound_path(value: str, key: str = 'startup_sound') -> Path
```

``default``: the packaged sound; anything else: a path (relative ones below the home).


<a id="lauschkiste.jingle.Jingle"></a>

## Jingle Objects

```python
class Jingle(CoreModule)
```

Plays the startup sound when ready and the shutdown sound when stopping.


<a id="lauschkiste.jingle.Jingle.play"></a>

#### play

```python
@action()
def play(sound: str) -> None
```

Play a sound file (path relative to the home directory or absolute).


<a id="lauschkiste.library.index"></a>

# lauschkiste.library.index

SQLite index of the music library: tags and durations read with mutagen.

Songs are keyed by their path relative to the music library root. A scan only re-reads files whose
modification time or size changed.


<a id="lauschkiste.library.index.read_tags"></a>

#### read\_tags

```python
def read_tags(path: Path) -> Dict[str, Any]
```

Title, artist, album, albumartist, track, disc and duration of an audio file (missing: None).


<a id="lauschkiste.library.index.LibraryIndex"></a>

## LibraryIndex Objects

```python
class LibraryIndex()
```

<a id="lauschkiste.library.index.LibraryIndex.relative"></a>

#### relative

```python
def relative(song_url: str) -> Optional[str]
```

``song_url`` (absolute below the root, or relative to it) as index key, else None.


<a id="lauschkiste.library.index.LibraryIndex.scan"></a>

#### scan

```python
def scan() -> ScanResult
```

Bring the index in line with the files on disk. Concurrent calls run one after another.


<a id="lauschkiste.library.index.LibraryIndex.albums"></a>

#### albums

```python
def albums(folder: str = '') -> List[Dict[str, Any]]
```

Albums below ``folder``, grouped by album artist (falling back to the artist) and album title.


<a id="lauschkiste.library.watch"></a>

# lauschkiste.library.watch

Notice changes to the music folder made outside Lauschkiste (Samba, USB stick, scp).


<a id="lauschkiste.library.watch.Snapshot"></a>

#### Snapshot

Per folder: its own modification time, the sum of its files' sizes, their newest modification time


<a id="lauschkiste.library.watch.snapshot"></a>

#### snapshot

```python
def snapshot(root: str) -> Snapshot
```

State of the folder tree below ``root``; growing files count as changes too.


<a id="lauschkiste.library.watch.Inotify"></a>

## Inotify Objects

```python
class Inotify()
```

Linux inotify on a folder tree: wakes up only when something below it changes.


<a id="lauschkiste.library.watch.Inotify.wait"></a>

#### wait

```python
def wait(timeout: float, wake_fd: int) -> bool
```

True if something changed within ``timeout`` seconds; returns early when ``wake_fd`` is readable.


<a id="lauschkiste.library.watch.FolderWatcher"></a>

## FolderWatcher Objects

```python
class FolderWatcher()
```

Calls ``on_change`` once the tree below ``root()`` changed and then stayed unchanged for one

interval. Uses inotify where available (no work while nothing changes); otherwise, or on file
systems where it can't be set up, it polls.


<a id="lauschkiste.library.files"></a>

# lauschkiste.library.files

Safe file operations within the library.


<a id="lauschkiste.library.files.LibraryError"></a>

## LibraryError Objects

```python
class LibraryError(OperationError)
```

An expected library operation failure suitable for an HTTP response.


<a id="lauschkiste.library.files.resolve_library_path"></a>

#### resolve\_library\_path

```python
def resolve_library_path(root,
                         value,
                         *,
                         allow_root=True,
                         require_exists=False)
```

Resolve a relative or internal absolute path without escaping ``root``.


<a id="lauschkiste.library.files.UploadSession"></a>

## UploadSession Objects

```python
class UploadSession()
```

Write one upload to a temporary file and publish it atomically.


<a id="lauschkiste.library.files.MusicLibrary"></a>

## MusicLibrary Objects

```python
class MusicLibrary()
```

Perform validated mutations beneath a lazily resolved library root.


<a id="lauschkiste.library.module"></a>

# lauschkiste.library.module

The library core module: file management, index, metadata, cover art and library sources.


<a id="lauschkiste.library.module.LibrarySource"></a>

## LibrarySource Objects

```python
class LibrarySource(Protocol)
```

Further music a player backend or plugin can play (e.g. an mpd database, a streaming service).


<a id="lauschkiste.library.module.LibrarySource.describe"></a>

#### describe

```python
def describe() -> Dict[str, Any]
```

``{'id', 'label', 'views': [{'id', 'label', 'kind': 'items'|'folders', 'content_types'}]}``


<a id="lauschkiste.library.module.LibrarySource.list_items"></a>

#### list\_items

```python
def list_items(content_types: Optional[List[str]]) -> List[Dict[str, Any]]
```

Items (albums, playlists, ...) with ``albumartist``, ``album``, ``content_type``, ``content_uri``.


<a id="lauschkiste.library.module.LibrarySource.cover"></a>

#### cover

```python
def cover(song_url: str) -> Optional[str]
```

URL of the song's cover (absolute or relative to the web app), or None.


<a id="lauschkiste.library.module.song_from_source"></a>

#### song\_from\_source

```python
def song_from_source(provider: str, data: Dict[str, Any]) -> Song
```

A :class:`Song` from a source's song mapping (mpd style keys are understood).


<a id="lauschkiste.library.module.Library"></a>

## Library Objects

```python
class Library(CoreModule)
```

Music library: files, index with metadata, cover art; further sources plug in at ``library.sources``.


<a id="lauschkiste.library.module.Library.list_entries"></a>

#### list\_entries

```python
@query(path='/api/v1/library/entries')
def list_entries(folder: str) -> LibraryEntries
```

Files and folders in a library folder.


<a id="lauschkiste.library.module.Library.create_folder"></a>

#### create\_folder

```python
@action(path='/api/v1/library/folders', status_code=201)
def create_folder(parent: str, name: str) -> CreatedFolder
```

Create a folder in the library.


<a id="lauschkiste.library.module.Library.delete_entries"></a>

#### delete\_entries

```python
@action(method='DELETE', path='/api/v1/library/entries')
def delete_entries(paths: List[str]) -> DeletedEntries
```

Delete files and folders from the library.


<a id="lauschkiste.library.module.Library.refresh"></a>

#### refresh

```python
@action(path='/api/v1/library/refresh')
def refresh() -> ScanStarted
```

Rescan the library (and refresh all other sources).


<a id="lauschkiste.library.module.Library.list_sources"></a>

#### list\_sources

```python
@query(path='/sources')
def list_sources() -> List[SourceInfo]
```

The local library and every registered source, with their views.


<a id="lauschkiste.library.module.Library.list_items"></a>

#### list\_items

```python
@query(path='/items')
def list_items(provider: Optional[str] = None,
               content_types: Optional[List[str]] = None) -> List[LibraryItem]
```

Albums (and other items) of one source or all of them.


<a id="lauschkiste.library.module.Library.list_songs"></a>

#### list\_songs

```python
@query(path='/songs')
def list_songs(albumartist: str,
               album: str,
               content_uri: Optional[str] = None,
               provider: Optional[str] = None) -> List[Song]
```

Songs of an album, in track order.


<a id="lauschkiste.library.module.Library.list_folder_songs"></a>

#### list\_folder\_songs

```python
@query(path='/folder-songs')
def list_folder_songs(folder: str) -> List[Song]
```

Songs of the local library below ``folder``.


<a id="lauschkiste.library.module.Library.get_song"></a>

#### get\_song

```python
@query(path='/song')
def get_song(song_url: str, provider: Optional[str] = None) -> Optional[Song]
```

Metadata of a single song, or null if it is unknown.


<a id="lauschkiste.library.module.Library.search"></a>

#### search

```python
@query(path='/search')
def search(query: str) -> List[Song]
```

Songs of the local library matching title, artist, album or path.


<a id="lauschkiste.library.module.Library.get_song_cover"></a>

#### get\_song\_cover

```python
@query(path='/cover/song')
def get_song_cover(song_url: str, provider: Optional[str] = None) -> CoverArt
```

Cover art URL of a song.


<a id="lauschkiste.library.module.Library.get_album_cover"></a>

#### get\_album\_cover

```python
@query(path='/cover/album')
def get_album_cover(albumartist: str,
                    album: str,
                    content_uri: Optional[str] = None,
                    provider: Optional[str] = None) -> CoverArt
```

Cover art URL of an album (the cover of its first song).


<a id="lauschkiste.library.module.Library.flush_covers"></a>

#### flush\_covers

```python
@action(path='/covers/flush')
def flush_covers() -> None
```

Delete all cached cover art; it is extracted again when needed.


<a id="lauschkiste.library.covers"></a>

# lauschkiste.library.covers

Cover art of songs: embedded pictures (MP3, FLAC, MP4, Ogg) or an image in the song's folder.


<a id="lauschkiste.library.covers.CoverCache"></a>

## CoverCache Objects

```python
class CoverCache()
```

Extracts covers into ``cache_dir`` once; names are content-independent hashes of the source.


<a id="lauschkiste.library.covers.CoverCache.cover_for"></a>

#### cover\_for

```python
def cover_for(song: Path) -> Optional[str]
```

File name in the cache of the song's cover, or None when it has none.


<a id="lauschkiste.library"></a>

# lauschkiste.library

The library: file management, index, metadata and cover art.


<a id="lauschkiste.library.root"></a>

#### root

```python
def root() -> str
```

The library directory, from ``library.path``.


<a id="lauschkiste.podcasts"></a>

# lauschkiste.podcasts

The podcasts core module: podcast feeds, episodes streamed and continued where they stopped.

Subscribed podcasts are kept in ``podcasts.podcasts_file``, the episodes of each feed are cached in
``podcasts.cache_dir`` and fetched again when older than ``refresh_minutes``. The position is kept
per episode; an episode played to the end counts as heard.


<a id="lauschkiste.podcasts.Podcast"></a>

## Podcast Objects

```python
class Podcast(BaseModel)
```

<a id="lauschkiste.podcasts.Podcast.hidden"></a>

#### hidden

taken off the "continue" list; it comes back with a new episode or when one is heard


<a id="lauschkiste.podcasts.Episode"></a>

## Episode Objects

```python
class Episode(BaseModel)
```

<a id="lauschkiste.podcasts.Episode.item"></a>

#### item

the item id at ``cache`` (the episode can be downloaded)


<a id="lauschkiste.podcasts.Episode.availability"></a>

#### availability

'stream' (played over the network) or 'cached' (downloaded to the box)


<a id="lauschkiste.podcasts.PodcastHit"></a>

## PodcastHit Objects

```python
class PodcastHit(BaseModel)
```

A podcast found in a directory.


<a id="lauschkiste.podcasts.SearchResult"></a>

## SearchResult Objects

```python
class SearchResult(BaseModel)
```

<a id="lauschkiste.podcasts.SearchResult.errors"></a>

#### errors

directory id -> why it gave no answer


<a id="lauschkiste.podcasts.PodcastDirectory"></a>

## PodcastDirectory Objects

```python
class PodcastDirectory(Protocol)
```

A place to find podcasts, registered at ``podcasts.directories`` by a plugin.


<a id="lauschkiste.podcasts.PodcastDirectory.search"></a>

#### search

```python
def search(term: str, limit: int) -> List[Dict[str, Any]]
```

Podcasts matching ``term`` as mappings with ``title``, ``feed_url`` and optionally ``author``, ``image``.


<a id="lauschkiste.podcasts.PodcastDirectory.top"></a>

#### top

```python
def top(limit: int) -> List[Dict[str, Any]]
```

Popular podcasts, same mappings.


<a id="lauschkiste.podcasts.EpisodeProvider"></a>

## EpisodeProvider Objects

```python
class EpisodeProvider()
```

``cache.providers`` entry ``podcasts``: an episode is the file of its feed entry.


<a id="lauschkiste.podcasts.parse_feed"></a>

#### parse\_feed

```python
def parse_feed(content: bytes) -> Dict[str, Any]
```

``{'title', 'image', 'episodes': [{'id', 'title', 'url', 'published', 'duration', 'image'}]}``,

newest episode first. Raises FeedError if ``content`` is not an RSS or Atom feed with audio.


<a id="lauschkiste.podcasts.Podcasts"></a>

## Podcasts Objects

```python
class Podcasts(CoreModule)
```

Podcasts: subscribe to feeds, play episodes and continue them.


<a id="lauschkiste.podcasts.Podcasts.list_podcasts"></a>

#### list\_podcasts

```python
@query(path='/')
def list_podcasts() -> List[Podcast]
```

All podcasts, by name, with the number of (unheard) episodes.


<a id="lauschkiste.podcasts.Podcasts.list_episodes"></a>

#### list\_episodes

```python
@query(path='/{podcast}/episodes')
def list_episodes(podcast: str) -> List[Episode]
```

Episodes of a podcast, newest first (the feed is fetched again when stale).


<a id="lauschkiste.podcasts.Podcasts.add_podcast"></a>

#### add\_podcast

```python
@action(path='/', status_code=201)
def add_podcast(url: str, name: Optional[str] = None) -> Podcast
```

Subscribe to a feed; the name defaults to the feed's title.


<a id="lauschkiste.podcasts.Podcasts.update_podcast"></a>

#### update\_podcast

```python
@action(method='PUT', path='/{podcast}')
def update_podcast(podcast: str, name: str) -> Podcast
```

Rename a podcast.


<a id="lauschkiste.podcasts.Podcasts.delete_podcast"></a>

#### delete\_podcast

```python
@action(method='DELETE', path='/{podcast}')
def delete_podcast(podcast: str) -> None
```

Unsubscribe from a podcast. Cards playing it stop working.


<a id="lauschkiste.podcasts.Podcasts.refresh"></a>

#### refresh

```python
@action(path='/refresh')
def refresh(podcast: Optional[str] = None) -> None
```

Fetch the episodes of one podcast, or of all.


<a id="lauschkiste.podcasts.Podcasts.list_directories"></a>

#### list\_directories

```python
@query(path='/directories')
def list_directories() -> List[DirectoryInfo]
```

The places podcasts can be searched in (added by plugins).


<a id="lauschkiste.podcasts.Podcasts.search"></a>

#### search

```python
@query(path='/search')
def search(term: str,
           directory: Optional[str] = None,
           limit: int = 20) -> SearchResult
```

Search the directories for podcasts.


<a id="lauschkiste.podcasts.Podcasts.top"></a>

#### top

```python
@query(path='/top')
def top(directory: Optional[str] = None, limit: int = 20) -> SearchResult
```

Popular podcasts of the directories.


<a id="lauschkiste.podcasts.Podcasts.import_opml"></a>

#### import\_opml

```python
@action(path='/import_opml')
def import_opml(content: str) -> ImportResult
```

Subscribe to all feeds of an OPML file (for example exported by AntennaPod). The episodes

are fetched in the background.


<a id="lauschkiste.podcasts.Podcasts.export_opml"></a>

#### export\_opml

```python
@query(path='/export_opml')
def export_opml() -> Opml
```

The subscriptions as an OPML file.


<a id="lauschkiste.podcasts.Podcasts.hide_from_continue"></a>

#### hide\_from\_continue

```python
@action()
def hide_from_continue(podcast: str) -> None
```

Take a podcast off the "continue" list until a new episode comes or one is heard.


<a id="lauschkiste.podcasts.Podcasts.play"></a>

#### play

```python
@action()
def play(podcast: str, episode: Optional[str] = None) -> None
```

Play an episode where it stopped; without ``episode`` the newest unheard one (or the

newest, when all are heard).


<a id="lauschkiste.podcasts.Podcasts.set_heard"></a>

#### set\_heard

```python
@action()
def set_heard(podcast: str, episode: str, heard: bool = True) -> None
```

Mark an episode as heard (or not); either way it starts from the beginning next time.


<a id="lauschkiste.directories"></a>

# lauschkiste.directories

Asking several directories at once and merging what they answer (podcast and radio directories).


<a id="lauschkiste.directories.ask"></a>

#### ask

```python
def ask(directories: Iterable[Tuple[str, Any]], only: Optional[str],
        call: Callable[[Any], List[Row]],
        what: str) -> Tuple[List[Tuple[str, List[Row]]], Dict[str, str]]
```

Ask all directories (or just ``only``) in parallel with ``call(directory)``.

Returns the rows of each directory and, for a directory that failed, why; one failing leaves the others.


<a id="lauschkiste.directories.interleave"></a>

#### interleave

```python
def interleave(answers: List[Tuple[str, List[Row]]],
               key_of: Callable[[Row], str],
               usable: Callable[[Row], bool],
               limit: Optional[int] = None) -> List[Row]
```

One list from the answers: the directories take turns (so that none fills it), duplicates (same ``key_of``)

are dropped, and every row gets the id of the directory it came from as ``directory``.


<a id="lauschkiste.radio_playlist"></a>

# lauschkiste.radio\_playlist

Station lists as ``.m3u`` and ``.pls`` files, which radio apps and players import and export.


<a id="lauschkiste.radio_playlist.parse_stations"></a>

#### parse\_stations

```python
def parse_stations(content: str) -> List[Dict[str, str]]
```

``[{"name", "url"}]`` of every stream in an M3U (with names from its EXTINF lines) or PLS playlist.

Raises ValueError if ``content`` has no stream or is too big.


<a id="lauschkiste.radio_playlist.render_m3u"></a>

#### render\_m3u

```python
def render_m3u(stations: Iterable[Dict[str, str]]) -> str
```

An extended M3U for ``{'name', 'url'}`` pairs.


<a id="lauschkiste.rfid.reader"></a>

# lauschkiste.rfid.reader

RFID reader framework: one thread per configured reader, card dispatch, card removal detection.

Hardware drivers register at the ``rfid.readers`` extension point. Readers are configured in the
reader config file (``rfid.reader_config``), each with the name of its driver under ``module``.


<a id="lauschkiste.rfid.reader.ReaderDriver"></a>

## ReaderDriver Objects

```python
class ReaderDriver(Protocol)
```

<a id="lauschkiste.rfid.reader.ReaderDriver.create_reader"></a>

#### create\_reader

```python
def create_reader(reader_cfg_key: str) -> Any
```

Return a reader for the reader config key: a context manager that iterates card ids

('' on timeout) and has ``stop()``.


<a id="lauschkiste.rfid.reader.ReaderSetting"></a>

## ReaderSetting Objects

```python
class ReaderSetting(BaseModel)
```

How a reader behaves; its driver and wiring (``module``, ``config``) are kept as they are.


<a id="lauschkiste.rfid.reader.CardDetected"></a>

## CardDetected Objects

```python
class CardDetected(BaseModel)
```

<a id="lauschkiste.rfid.reader.CardDetected.learned"></a>

#### learned

Detected while learning: its action did not run


<a id="lauschkiste.rfid.reader.CardRemovalTimer"></a>

## CardRemovalTimer Objects

```python
class CardRemovalTimer(threading.Thread)
```

Runs ``on_timeout`` once when the card has not been seen for about a second.


<a id="lauschkiste.rfid.reader.Rfid"></a>

## Rfid Objects

```python
class Rfid(CoreModule)
```

RFID readers: detect cards and run their actions.


<a id="lauschkiste.rfid.reader.Rfid.claims"></a>

#### claims

```python
def claims() -> List[Claim]
```

Pins and buses of the configured readers whose driver says what it uses.


<a id="lauschkiste.rfid.reader.Rfid.resolve_config_action"></a>

#### resolve\_config\_action

```python
def resolve_config_action(entry, where: str) -> Optional[Callable[[], Any]]
```

Turn a configured action (new or old format) into a callable, or None if invalid.


<a id="lauschkiste.rfid.reader.Rfid.learn"></a>

#### learn

```python
@action(path='/learn')
def learn(seconds: float = 60.0) -> None
```

Report the next card within ``seconds`` (``learned``) without running its action.


<a id="lauschkiste.rfid.reader.Rfid.stop_learning"></a>

#### stop\_learning

```python
@action(path='/learn/stop')
def stop_learning() -> None
```

End learning; cards run their actions again.


<a id="lauschkiste.rfid.reader.Rfid.list_readers"></a>

#### list\_readers

```python
@query(path='/readers')
def list_readers() -> Dict[str, str]
```

Configured readers and their driver.


<a id="lauschkiste.rfid.readerbase"></a>

# lauschkiste.rfid.readerbase

<a id="lauschkiste.rfid.readerbase.ReaderBaseClass"></a>

## ReaderBaseClass Objects

```python
class ReaderBaseClass(ABC)
```

Abstract Base Class for all Reader Classes to ensure common API

Look at template_new_reader.py for documentation how to integrate a new RFID reader


<a id="lauschkiste.rfid"></a>

# lauschkiste.rfid

<a id="lauschkiste.rfid.cards"></a>

# lauschkiste.rfid.cards

The RFID card database: which action a card triggers.

Entries are stored as ``action: <module>.<action>`` plus named ``args``.


<a id="lauschkiste.rfid.cards.Cards"></a>

## Cards Objects

```python
class Cards(CoreModule)
```

Card database: register, list and delete cards.


<a id="lauschkiste.rfid.cards.Cards.list_cards"></a>

#### list\_cards

```python
@query(path='/api/v1/cards')
def list_cards() -> Dict[str, CardInfo]
```

All registered cards with their action and whether it is currently available.


<a id="lauschkiste.rfid.cards.Cards.get_card"></a>

#### get\_card

```python
@query(path='/api/v1/cards/{card_id}')
def get_card(card_id: str) -> Optional[CardEntry]
```

The card's entry, or null when it is unknown or its action is unavailable.


<a id="lauschkiste.rfid.cards.Cards.register_card"></a>

#### register\_card

```python
@action(path='/api/v1/cards')
def register_card(card_id: str,
                  action: str,
                  args: Optional[Dict[str, Any]] = None,
                  ignore_same_id_delay: bool = False,
                  ignore_card_removal_action: bool = False,
                  overwrite: bool = False) -> None
```

Register a card to trigger an action.


<a id="lauschkiste.rfid.cards.Cards.delete_card"></a>

#### delete\_card

```python
@action(method='DELETE', path='/api/v1/cards/{card_id}')
def delete_card(card_id: str) -> None
```

Delete a card.


<a id="lauschkiste.rfid.cardutils"></a>

# lauschkiste.rfid.cardutils

Readable descriptions of card database entries.


<a id="lauschkiste.rfid.cardutils.card_command_to_str"></a>

#### card\_command\_to\_str

```python
def card_command_to_str(entry: Mapping[str, Any],
                        long: bool = False) -> List[str]
```

``[action(args)]``, plus the card flags when ``long`` is set.


<a id="lauschkiste.audiobooks"></a>

# lauschkiste.audiobooks

The audiobooks core module: audiobooks in ``library/audiobooks``, continued where they stopped.

Each folder directly below ``audiobooks`` is one audiobook, its files are the chapters in file name
order. The position is kept per audiobook in ``audiobooks.state_file``; chapters play in order,
regardless of shuffle and repeat.


<a id="lauschkiste.audiobooks.AudiobookSource"></a>

## AudiobookSource Objects

```python
class AudiobookSource(Protocol)
```

Audiobooks from somewhere else (e.g. a server), registered at ``audiobooks.sources`` under the

source id. Their position is kept by the source, not in ``audiobooks.state_file``.


<a id="lauschkiste.audiobooks.AudiobookSource.list_books"></a>

#### list\_books

```python
def list_books() -> List[Dict[str, Any]]
```

The books as mappings with the fields of :class:`Audiobook` (``source`` is added).


<a id="lauschkiste.audiobooks.AudiobookSource.files"></a>

#### files

```python
def files(book: str) -> List[str]
```

The track URLs to play, in order; raises :class:`OperationError` if there is no such book.


<a id="lauschkiste.audiobooks.AudiobookSource.title"></a>

#### title

```python
def title(book: str) -> str
```

The title shown while it plays.


<a id="lauschkiste.audiobooks.AudiobookSource.position"></a>

#### position

```python
def position(book: str) -> Any
```

A ``lauschkiste.resume.PositionStore`` for the book.


<a id="lauschkiste.audiobooks.AudiobookSource.set_finished"></a>

#### set\_finished

```python
def set_finished(book: str, finished: bool) -> None
```

Mark the book finished or not (either way it starts from the beginning next time).


<a id="lauschkiste.audiobooks.Audiobook"></a>

## Audiobook Objects

```python
class Audiobook(BaseModel)
```

<a id="lauschkiste.audiobooks.Audiobook.availability"></a>

#### availability

'local' (a folder of the library), 'cached' (downloaded from the source) or 'stream' (played over the network)


<a id="lauschkiste.audiobooks.Audiobook.hidden"></a>

#### hidden

taken off the "continue" list; it comes back when the book is played on


<a id="lauschkiste.audiobooks.Audiobooks"></a>

## Audiobooks Objects

```python
class Audiobooks(CoreModule)
```

Audiobooks: play, continue, start over, mark as finished.


<a id="lauschkiste.audiobooks.Audiobooks.list_books"></a>

#### list\_books

```python
@query(path='/')
def list_books() -> List[Audiobook]
```

All audiobooks with their progress.


<a id="lauschkiste.audiobooks.Audiobooks.play"></a>

#### play

```python
@action()
def play(book: str, source: str = LOCAL) -> None
```

Play an audiobook where it stopped (from the beginning when it is new or finished).


<a id="lauschkiste.audiobooks.Audiobooks.hide_from_continue"></a>

#### hide\_from\_continue

```python
@action()
def hide_from_continue(book: str, source: str = LOCAL) -> None
```

Take an audiobook off the "continue" list until it is played on.


<a id="lauschkiste.audiobooks.Audiobooks.restart"></a>

#### restart

```python
@action()
def restart(book: str, source: str = LOCAL) -> None
```

Play an audiobook from the beginning.


<a id="lauschkiste.audiobooks.Audiobooks.set_finished"></a>

#### set\_finished

```python
@action()
def set_finished(book: str,
                 finished: bool = True,
                 source: str = LOCAL) -> None
```

Mark an audiobook as finished (or not); either way it starts from the beginning next time.


<a id="lauschkiste.volume"></a>

# lauschkiste.volume

The volume core module: volume, mute, soft maximum, output selection and fade-out.

The mixer is PulseAudio/PipeWire (via pulsectl) when a server is reachable, otherwise the volume of
the active player backend.


<a id="lauschkiste.volume.PlayerMixer"></a>

## PlayerMixer Objects

```python
class PlayerMixer()
```

Volume of the active player backend; no outputs to choose from.


<a id="lauschkiste.volume.PulseMixer"></a>

## PulseMixer Objects

```python
class PulseMixer()
```

PulseAudio/PipeWire default sink; ``volume_limit`` of an output scales 0..100 to 0..limit.


<a id="lauschkiste.volume.pulse_sinks"></a>

#### pulse\_sinks

```python
def pulse_sinks() -> List[Choice]
```

Sinks of the PulseAudio/PipeWire server; empty if there is none.


<a id="lauschkiste.volume.Volume"></a>

## Volume Objects

```python
class Volume(CoreModule)
```

Volume, mute, soft maximum and audio output.


<a id="lauschkiste.volume.Volume.get_volume"></a>

#### get\_volume

```python
@query(path='')
def get_volume() -> VolumeState
```

Current volume, mute state and soft maximum.


<a id="lauschkiste.volume.Volume.set_volume"></a>

#### set\_volume

```python
@action(method='PUT', path='')
def set_volume(volume: int) -> VolumeState
```

Set the volume (0-100, limited to the soft maximum).


<a id="lauschkiste.volume.Volume.change_volume"></a>

#### change\_volume

```python
@action(path='/change')
def change_volume(step: int = 5) -> VolumeState
```

Change the volume by ``step`` (negative to lower it).


<a id="lauschkiste.volume.Volume.mute"></a>

#### mute

```python
@action(path='/mute')
def mute(mute: Optional[bool] = None) -> VolumeState
```

Mute or unmute; toggles when ``mute`` is left out.


<a id="lauschkiste.volume.Volume.list_sinks"></a>

#### list\_sinks

```python
@query(path='/sinks')
def list_sinks() -> List[Choice]
```

Audio devices of the PulseAudio/PipeWire server, for choosing outputs.


<a id="lauschkiste.volume.Volume.set_soft_max_volume"></a>

#### set\_soft\_max\_volume

```python
@action(method='PUT', path='/soft-max')
def set_soft_max_volume(max_volume: int) -> VolumeState
```

Limit the volume that can be set (0-100); lowers the current volume if needed.


<a id="lauschkiste.volume.Volume.get_outputs"></a>

#### get\_outputs

```python
@query(path='/outputs')
def get_outputs() -> OutputsState
```

Configured outputs that are available right now.


<a id="lauschkiste.volume.Volume.set_output"></a>

#### set\_output

```python
@action(method='PUT', path='/outputs/active')
def set_output(name: str) -> OutputsState
```

Switch the audio output.


<a id="lauschkiste.volume.Volume.toggle_output"></a>

#### toggle\_output

```python
@action(path='/outputs/toggle')
def toggle_output() -> OutputsState
```

Switch to the next available output.


<a id="lauschkiste.volume.Volume.fade_out"></a>

#### fade\_out

```python
@action(path='/fade-out')
def fade_out(seconds: float = 10.0) -> None
```

Lower the volume to zero over ``seconds``, stop playback, then restore the volume.


<a id="lauschkiste.startup"></a>

# lauschkiste.startup

Start-up helpers for small boards.


<a id="lauschkiste.startup.import_fastapi"></a>

#### import\_fastapi

```python
def import_fastapi() -> None
```

Import FastAPI with the schemas of its OpenAPI models built on first use instead of now.

They are only needed for ``/openapi.json``; building them at import takes seconds on a Pi Zero.


<a id="lauschkiste.nv_manager"></a>

# lauschkiste.nv\_manager

<a id="lauschkiste.dismissed"></a>

# lauschkiste.dismissed

What was taken off the "continue" list: an item stays off until its progress changes.


<a id="lauschkiste.dismissed.Dismissed"></a>

## Dismissed Objects

```python
class Dismissed()
```

``key -> marker`` in a JSON file. The marker says how far the item was when it was taken off; an item whose

marker differs from the saved one (it was played on, a new episode came) is back on the list.


<a id="lauschkiste.radio"></a>

# lauschkiste.radio

The radio core module: internet radio stations, one per card.

Stations are kept in ``radio.stations_file``. A station URL may point to the stream itself or to an
``.m3u``/``.pls`` playlist, which is resolved to its first stream when the station is played.


<a id="lauschkiste.radio.Station"></a>

## Station Objects

```python
class Station(BaseModel)
```

<a id="lauschkiste.radio.Station.last_played"></a>

#### last\_played

when it was last played (UTC); empty for a station never played here or taken off the "continue" list


<a id="lauschkiste.radio.StationHit"></a>

## StationHit Objects

```python
class StationHit(BaseModel)
```

A station found in a directory.


<a id="lauschkiste.radio.StationHit.added"></a>

#### added

already one of the stations


<a id="lauschkiste.radio.SearchResult"></a>

## SearchResult Objects

```python
class SearchResult(BaseModel)
```

<a id="lauschkiste.radio.SearchResult.errors"></a>

#### errors

directory id -> why it gave no answer


<a id="lauschkiste.radio.RadioDirectory"></a>

## RadioDirectory Objects

```python
class RadioDirectory(Protocol)
```

A place to find stations, registered at ``radio.directories`` by a plugin.


<a id="lauschkiste.radio.RadioDirectory.search"></a>

#### search

```python
def search(term: str, limit: int) -> List[Dict[str, Any]]
```

Stations matching ``term`` as mappings with ``name`` and ``url``, optionally ``logo``, ``country``, ``tags``,

``codec`` and ``bitrate``.


<a id="lauschkiste.radio.RadioDirectory.top"></a>

#### top

```python
def top(limit: int) -> List[Dict[str, Any]]
```

Popular stations, same mappings.


<a id="lauschkiste.radio.streams_in_playlist"></a>

#### streams\_in\_playlist

```python
def streams_in_playlist(text: str) -> List[str]
```

Stream URLs of an ``.m3u`` or ``.pls`` playlist, in order.


<a id="lauschkiste.radio.Radio"></a>

## Radio Objects

```python
class Radio(CoreModule)
```

Internet radio stations.


<a id="lauschkiste.radio.Radio.list_stations"></a>

#### list\_stations

```python
@query(path='/stations')
def list_stations() -> List[Station]
```

All stations, by name.


<a id="lauschkiste.radio.Radio.add_station"></a>

#### add\_station

```python
@action(path='/stations', status_code=201)
def add_station(name: str, url: str, logo: Optional[str] = None) -> Station
```

Add a station; its id is derived from the name.


<a id="lauschkiste.radio.Radio.update_station"></a>

#### update\_station

```python
@action(method='PUT', path='/stations/{station}')
def update_station(station: str,
                   name: Optional[str] = None,
                   url: Optional[str] = None,
                   logo: Optional[str] = None) -> Station
```

Change a station; fields left out stay unchanged, an empty ``logo`` removes the logo.


<a id="lauschkiste.radio.Radio.delete_station"></a>

#### delete\_station

```python
@action(method='DELETE', path='/stations/{station}')
def delete_station(station: str) -> None
```

Delete a station. Cards playing it stop working.


<a id="lauschkiste.radio.Radio.list_directories"></a>

#### list\_directories

```python
@query(path='/directories')
def list_directories() -> List[DirectoryInfo]
```

The places stations can be searched in (added by plugins).


<a id="lauschkiste.radio.Radio.search"></a>

#### search

```python
@query(path='/search')
def search(term: str,
           directory: Optional[str] = None,
           limit: int = 20) -> SearchResult
```

Search the directories for stations.


<a id="lauschkiste.radio.Radio.top"></a>

#### top

```python
@query(path='/top')
def top(directory: Optional[str] = None, limit: int = 20) -> SearchResult
```

Popular stations of the directories.


<a id="lauschkiste.radio.Radio.import_playlist"></a>

#### import\_playlist

```python
@action(path='/import_playlist')
def import_playlist(content: str) -> ImportResult
```

Add all streams of an M3U or PLS file as stations; known addresses are skipped.


<a id="lauschkiste.radio.Radio.export_playlist"></a>

#### export\_playlist

```python
@query(path='/export_playlist')
def export_playlist() -> Playlist
```

The stations as an M3U file.


<a id="lauschkiste.radio.Radio.play"></a>

#### play

```python
@action()
def play(station: str) -> None
```

Play a station.


<a id="lauschkiste.radio.Radio.forget_recent"></a>

#### forget\_recent

```python
@action()
def forget_recent(station: str) -> None
```

Take a station off the "continue" list (it stays a station).


<a id="lauschkiste.publishing.bus"></a>

# lauschkiste.publishing.bus

Thread-safe in-process pub/sub bus with last-value caching.

`publish()` can be called from any thread (components run in RFID reader threads, timer threads,
etc.); subscriber callbacks are invoked synchronously on the publishing thread, so they must be
fast and must not block. The FastAPI bridge hands off to its own event loop via
`asyncio.run_coroutine_threadsafe` rather than doing any real work in the callback itself.


<a id="lauschkiste.publishing.bus.EventBus"></a>

## EventBus Objects

```python
class EventBus()
```

<a id="lauschkiste.publishing.bus.EventBus.publish"></a>

#### publish

```python
def publish(topic: str, payload: Optional[Any]) -> None
```

Publish `payload` for `topic`. `payload=None` revokes the topic.


<a id="lauschkiste.publishing.bus.EventBus.resend"></a>

#### resend

```python
def resend(topic_prefix: str = '') -> None
```

Re-send all cached topics under `topic_prefix` to every subscriber.


<a id="lauschkiste.publishing.bus.EventBus.cache_snapshot"></a>

#### cache\_snapshot

```python
def cache_snapshot() -> Dict[str, Any]
```

A shallow copy of the full last-value cache, for a client that just subscribed.


<a id="lauschkiste.publishing"></a>

# lauschkiste.publishing

The process-wide event bus. Modules publish through their ``Context``, not directly.


<a id="lauschkiste.publishing.get_bus"></a>

#### get\_bus

```python
def get_bus() -> EventBus
```

The shared, thread-safe event bus.


<a id="lauschkiste.cache.worker"></a>

# lauschkiste.cache.worker

Downloads the files of one item into its folder. Runs as a process of its own, with the lowest priority.

python -m lauschkiste.cache.worker DEST RATE_FILE

``DEST/plan.json`` (readable for the user only, removed when the worker ends) lists the files with their address,
size and request headers. ``RATE_FILE`` holds the speed limit in kB/s (empty or 0: none, -1: wait) and is read
again while downloading. Progress goes to ``DEST/status.json``; files are renamed into place when complete and
``meta.json`` marks the item as complete.


<a id="lauschkiste.cache.worker.Download"></a>

## Download Objects

```python
class Download()
```

<a id="lauschkiste.cache.worker.Download.fetch"></a>

#### fetch

```python
def fetch(url: str, headers: Dict[str, str], target: Path, size: int) -> int
```

Download one file; returns its size. Without a known ``size`` the file is loaded from the start

(a listed size is often wrong) and the length it ends up with counts.


<a id="lauschkiste.cache.manager"></a>

# lauschkiste.cache.manager

Runs the worker process for one item after the other.


<a id="lauschkiste.cache"></a>

# lauschkiste.cache

The cache core module: items of a source (an audiobook, an episode, ...) downloaded to the box.

A plugin or module that can provide content for download registers a provider at ``cache.providers`` under
its source id. The module fetches what the provider's plan lists, in a process of its own with the lowest
priority, keeps the space limit and shows the state.


<a id="lauschkiste.cache.CacheFile"></a>

## CacheFile Objects

```python
class CacheFile(BaseModel)
```

<a id="lauschkiste.cache.CacheFile.size"></a>

#### size

bytes; 0 when the source does not know (the size is then taken from the download)


<a id="lauschkiste.cache.CacheProvider"></a>

## CacheProvider Objects

```python
class CacheProvider(Protocol)
```

<a id="lauschkiste.cache.CacheProvider.plan"></a>

#### plan

```python
def plan(item: str) -> CachePlan
```

The files that make up an item, with the headers to fetch them; raises :class:`OperationError`.


<a id="lauschkiste.cache.CacheProvider.version"></a>

#### version

```python
def version(item: str) -> Optional[str]
```

A value that changes when the server's copy of the item changes (from what is already known; no request).


<a id="lauschkiste.cache.CacheProvider.removable"></a>

#### removable

```python
def removable(item: str) -> bool
```

Whether the item may be removed to make room (for example finished or heard). Never for one in progress.


<a id="lauschkiste.cache.Cache"></a>

## Cache Objects

```python
class Cache(CoreModule)
```

Downloads items of a source to the box, so that they play without the network.


<a id="lauschkiste.cache.Cache.downloads"></a>

#### downloads

```python
@query(path='/downloads')
def downloads(source: Optional[str] = None) -> Downloads
```

Downloaded and downloading items and the space they use.


<a id="lauschkiste.cache.Cache.files"></a>

#### files

```python
@query(path='/files')
def files(source: str, item: str) -> Optional[CachedItem]
```

The files of a complete download (in order), or nothing.


<a id="lauschkiste.cache.Cache.cached"></a>

#### cached

```python
@query(path='/cached')
def cached(source: str) -> List[CachedItem]
```

All complete downloads of a source.


<a id="lauschkiste.cache.Cache.download"></a>

#### download

```python
@action()
def download(source: str, item: str) -> None
```

Download an item so that it plays without the network.


<a id="lauschkiste.cache.Cache.cancel"></a>

#### cancel

```python
@action()
def cancel(source: str, item: str) -> None
```

Stop a download; what was loaded is kept and continued next time.


<a id="lauschkiste.cache.Cache.remove"></a>

#### remove

```python
@action()
def remove(source: str, item: str) -> None
```

Delete the downloaded files of an item.


<a id="lauschkiste.cache.store"></a>

# lauschkiste.cache.store

The folder of downloaded items: ``<root>/<source>/<item>/``.


<a id="lauschkiste.cache.store.INTERNAL"></a>

#### INTERNAL

Files of the cache machinery itself; they do not count as used space


<a id="lauschkiste.cache.store.CacheStore"></a>

## CacheStore Objects

```python
class CacheStore()
```

<a id="lauschkiste.cache.store.CacheStore.complete"></a>

#### complete

```python
def complete(source: str, item: str) -> Optional[Dict[str, Any]]
```

The metadata of a complete download whose files are all there, else None.


<a id="lauschkiste.cache.store.CacheStore.items"></a>

#### items

```python
def items(source: Optional[str] = None) -> List[Tuple[str, str]]
```

``(source, item)`` of every folder, complete or not.


<a id="lauschkiste.cache.store.CacheStore.set_rate"></a>

#### set\_rate

```python
def set_rate(kbps: float) -> None
```

The speed limit of the worker in kB/s: 0 none, -1 wait.


<a id="lauschkiste.playlistgenerator"></a>

# lauschkiste.playlistgenerator

Playlists are build from directory content in the following way:

a directory is parsed and files are added to the playlist in the following way

1. files are added in alphabetic order
2. files ending with ``*.m3u`` are treated as folder playlist. Regular folder processing is suspended and the playlist
   is build solely from the ``*.m3u`` content. Only the alphabetically first ``*.m3u`` is processed. URLs are added verbatim

All files are treated as music files and are added to the playlist, except those:

 * starting with ``.``,
 * not having a file ending, i.e. do not contain a ``.``,
 * ending with ``.txt``,
 * ending with ``.m3u``,
 * ending with one of the excluded file endings in :attr:`PlaylistCollector._exclude_endings`

In recursive mode, the playlist is generated by concatenating all sub-folder playlists. Sub-folders are parsed
in alphabetic order. Symbolic links are being followed. The above rules are enforced on a per-folder bases.
This means, one ``*.m3u`` file per sub-folder is processed (if present).

In ``*.m3u`` files, all lines starting with ``#`` are ignored.


<a id="lauschkiste.playlistgenerator.TYPE_DECODE"></a>

#### TYPE\_DECODE

Types if file entires in parsed directory


<a id="lauschkiste.playlistgenerator.PlaylistCollector"></a>

## PlaylistCollector Objects

```python
class PlaylistCollector()
```

Build a playlist from directory(s)

This class is intended to be used with an absolute path to the music library::

    plc = PlaylistCollector('/home/chris/music')
    plc.parse('Traumfaenger')
    print(f"res = {plc}")

But it can also be used with relative paths from current working directory::

    plc = PlaylistCollector('.')
    plc.parse('../../../../music/Traumfaenger')
    print(f"res = {plc}")

The file ending exclusion list :attr:`PlaylistCollector._exclude_endings` is a class variable for performance reasons.
If changed it will affect all instances. For modifications always call :func:`set_exclusion_endings`.


<a id="lauschkiste.playlistgenerator.PlaylistCollector.__init__"></a>

#### \_\_init\_\_

```python
def __init__(music_library_base_path='/')
```

Initialize the playlist generator with music_library_base_path

**Arguments**:

- `music_library_base_path`: Base path the the music library. This is used to locate the file in the disk
but is omitted when generating the playlist entries. I.e. all files in the playlist are relative to this base dir

<a id="lauschkiste.playlistgenerator.PlaylistCollector.set_exclusion_endings"></a>

#### set\_exclusion\_endings

```python
@classmethod
def set_exclusion_endings(cls, endings: List[str])
```

Set the class-wide file ending exclusion list

See :attr:`PlaylistCollector._exclude_endings`


<a id="lauschkiste.playlistgenerator.PlaylistCollector.get_directory_content"></a>

#### get\_directory\_content

```python
def get_directory_content(path='.')
```

Parse the folder ``path`` and create a content list. Depth is always the current level

**Arguments**:

- `path`: Path to folder **relative** to ``music_library_base_path``

**Returns**:

[ { type: 'directory', name: 'Simone', path: '/some/path/to/Simone' }, {...} ]
where type is one of :attr:`TYPE_DECODE`

<a id="lauschkiste.playlistgenerator.PlaylistCollector.parse"></a>

#### parse

```python
def parse(path='.', recursive=False)
```

Parse the folder ``path`` and create a playlist from its content

**Arguments**:

- `path`: Path to folder **relative** to ``music_library_base_path``
- `recursive`: Parse folder recursivley, or stay in top-level folder

<a id="lauschkiste.api.events"></a>

# lauschkiste.api.events

Transport-neutral pieces of the browser events-over-websocket bridge (no web framework involved).


<a id="lauschkiste.api.events.EventBroker"></a>

## EventBroker Objects

```python
class EventBroker()
```

Maintain browser subscriptions, backed by the shared :class:`lauschkiste.publishing.bus.EventBus`.

Register :meth:`publish` as a bus subscriber callback (``bus.register(broker.publish)``); the
bus already delivers `payload=None` for revocations and calls this from whatever thread
published, so no separate transport bridging is needed here.


<a id="lauschkiste.api.events.EventBroker.publish"></a>

#### publish

```python
def publish(topic, payload)
```

Bus subscriber callback. `payload=None` means the topic was revoked.


<a id="lauschkiste.api.events.parse_subscription_command"></a>

#### parse\_subscription\_command

```python
def parse_subscription_command(command)
```

Validate a decoded events-websocket command.

**Raises**:

- `ValueError`: if the command is not a well-formed subscribe/unsubscribe request

**Returns**:

``(command_type, topics)``

<a id="lauschkiste.api"></a>

# lauschkiste.api

HTTP and WebSocket API for browser clients.


<a id="lauschkiste.api.fastapi_server"></a>

# lauschkiste.api.fastapi\_server

FastAPI + uvicorn HTTP and WebSocket API server.

The sole browser-facing HTTP/WebSocket bridge. Serves health, the routes of the modules (see
lauschkiste.contract.routes), events-over-websocket and (see lauschkiste.api.webapp_static) the webapp's
static build + /logs -- this is the one thing reachable from the LAN, hence `api.bind_address`
defaulting to 0.0.0.0.

Handlers run on a multi-worker executor; each module guards itself (see the contract's threading
model), so a slow call doesn't serialize the rest of the API.


<a id="lauschkiste.api.fastapi_server.default_webapp_build_dir"></a>

#### default\_webapp\_build\_dir

```python
def default_webapp_build_dir() -> Path
```

``api.webapp_dir``, else ``$LAUSCHKISTE_WEBAPP_DIR``, else the web app shipped in the package,

else the build directory of a source checkout.


<a id="lauschkiste.api.fastapi_server.BodySizeLimit"></a>

## BodySizeLimit Objects

```python
class BodySizeLimit()
```

Reject request bodies above ``limit`` bytes with 413 (except for streaming upload paths).


<a id="lauschkiste.api.fastapi_server.FastApiServer"></a>

## FastApiServer Objects

```python
class FastApiServer(threading.Thread)
```

Run the browser API on an isolated asyncio event loop.


<a id="lauschkiste.api.fastapi_server.FastApiServer.start_and_wait"></a>

#### start\_and\_wait

```python
def start_and_wait(timeout=120)
```

The timeout only catches a hung start; slow boards (Pi Zero) need well over 5 s.


<a id="lauschkiste.api.webapp_static"></a>

# lauschkiste.api.webapp\_static

Serve the built webapp, its fallback pages, and the /logs directory directly from FastAPI.

Serves the webapp's static build, a "build missing"/generic-404 fallback page and a /logs
directory listing. Unknown paths get the 404 page; there is no SPA deep-link fallback to index.html.


<a id="lauschkiste.api.webapp_static.HASHED_ASSETS_DIR"></a>

#### HASHED\_ASSETS\_DIR

Vite puts content-hashed files here; a new build gives them new names.


<a id="lauschkiste.api.webapp_static.CACHE_NEVER"></a>

#### CACHE\_NEVER

Everything else keeps its name across versions, and packaged files all carry the same

modification time, so neither heuristic caching nor revalidation would notice an update.


<a id="lauschkiste.api.webapp_static.register_webapp_routes"></a>

#### register\_webapp\_routes

```python
def register_webapp_routes(app: FastAPI, *, build_dir: Path,
                           logs_dir: Path) -> None
```

Mount the webapp build's static assets, index.html, a generic 404, and /logs. Call once.


<a id="lauschkiste.version"></a>

# lauschkiste.version

<a id="lauschkiste.version.version"></a>

#### version

```python
def version()
```

Return the Lauschkiste version as a string


<a id="lauschkiste.version.version_info"></a>

#### version\_info

```python
def version_info()
```

Return the Lauschkiste version as a tuple of three numbers

If this is a development version, an identifier string will be appended after the third integer.


<a id="lauschkiste.podcast_opml"></a>

# lauschkiste.podcast\_opml

OPML, the list format podcast apps (AntennaPod and others) import and export their subscriptions with.


<a id="lauschkiste.podcast_opml.normalize_url"></a>

#### normalize\_url

```python
def normalize_url(url: str) -> str
```

A feed address for comparing: scheme and host in lower case, no fragment, no trailing slash.


<a id="lauschkiste.podcast_opml.parse_opml"></a>

#### parse\_opml

```python
def parse_opml(content: str) -> List[Dict[str, str]]
```

``[{'title', 'url'}]`` of every feed in an OPML document (outlines may be nested in folders).

Raises ValueError if ``content`` is not OPML.


<a id="lauschkiste.podcast_opml.render_opml"></a>

#### render\_opml

```python
def render_opml(podcasts: Iterable[Tuple[str, str]],
                title: str = 'Lauschkiste') -> str
```

OPML 2.0 for ``(name, feed address)`` pairs.


<a id="lauschkiste.cfghandler"></a>

# lauschkiste.cfghandler

This module handles global and local configuration data

The concept is that config handler is created and initialized once in the main thread::

    cfg = get_handler('global')
    load_yaml(cfg, 'filename.yaml')

In all other modules (in potentially different threads) the same handler is obtained and used by::

    cfg = get_handler('global')

This eliminates the need to pass an effectively global configuration handler by parameters across the entire design.
Handlers are identified by their name (in the above example *global*)

The function :func:`get_handler` is the main entry point to obtain a new or existing handler.


<a id="lauschkiste.cfghandler.ConfigHandler"></a>

## ConfigHandler Objects

```python
class ConfigHandler()
```

The configuration handler class

Don't instantiate directly. Always use :func:`get_handler`!

**Threads:**

All threads can read and write to the configuration data.
**Proper thread-safeness must be ensured** by the the thread modifying the data by acquiring the lock
Easiest and best way is to use the context handler::

    with cfg:
       cfg['key'] = 66
       cfg.setndefault('hello', value='world')

For a single function call, this is done implicitly. In this case, there is no need
to explicitly acquire the lock.

Alternatively, you can lock and release manually by using :func:`acquire` and :func:`release`
But be very sure to release the lock even in cases of errors an exceptions!
Else we have a deadlock.

Reading may be done without acquiring a lock. But be aware that when reading multiple values without locking, another
thread may intervene and modify some values in between! So, locking is still recommended.


<a id="lauschkiste.cfghandler.ConfigHandler.loaded_from"></a>

#### loaded\_from

```python
@property
def loaded_from() -> Optional[str]
```

Property to store filename from which the config was loaded


<a id="lauschkiste.cfghandler.ConfigHandler.get"></a>

#### get

```python
def get(key, *, default=None)
```

Enforce keyword on default to avoid accidental misuse when actually getn is wanted


<a id="lauschkiste.cfghandler.ConfigHandler.setdefault"></a>

#### setdefault

```python
def setdefault(key, *, value)
```

Enforce keyword on default to avoid accidental misuse when actually setndefault is wanted


<a id="lauschkiste.cfghandler.ConfigHandler.getn"></a>

#### getn

```python
def getn(*keys, default=None)
```

Get the value at arbitrary hierarchy depth. Return ``default`` if key not present

The *default* value is returned no matter at which hierarchy level the path aborts.
A hierarchy is considered as any type with a :func:`get` method.


<a id="lauschkiste.cfghandler.ConfigHandler.setn"></a>

#### setn

```python
def setn(*keys, value, hierarchy_type=None) -> None
```

Set the ``key: value`` pair at arbitrary hierarchy depth

All non-existing hierarchy levels are created.

**Arguments**:

- `keys`: Key hierarchy path through the nested levels
- `value`: The value to set
- `hierarchy_type`: The type for new hierarchy levels. If *None*, the top-level type
is used

<a id="lauschkiste.cfghandler.ConfigHandler.setndefault"></a>

#### setndefault

```python
def setndefault(*keys, value, hierarchy_type=None)
```

Set the ``key: value`` pair at arbitrary hierarchy depth unless the key already exists

All non-existing hierarchy levels are created.

**Arguments**:

- `keys`: Key hierarchy path through the nested levels
- `value`: The default value to set
- `hierarchy_type`: The type for new hierarchy levels. If *None*, the top-level type
is used

**Returns**:

The actual value or or the default value if key does not exit

<a id="lauschkiste.cfghandler.ConfigHandler.config_dict"></a>

#### config\_dict

```python
def config_dict(data)
```

Initialize configuration data from dict-like data structure

**Arguments**:

- `data`: configuration data

<a id="lauschkiste.cfghandler.ConfigHandler.is_modified"></a>

#### is\_modified

```python
def is_modified() -> bool
```

Check if the data has changed since the last load/store

> [!NOTE]
> This relies on the *__str__* representation of the underlying data structure
> In case of ruamel, this ignores comments and only looks at the data


<a id="lauschkiste.cfghandler.ConfigHandler.clear_modified"></a>

#### clear\_modified

```python
def clear_modified() -> None
```

Sets the current state as new baseline, clearing the is_modified state


<a id="lauschkiste.cfghandler.ConfigHandler.save"></a>

#### save

```python
def save(only_if_changed: bool = False) -> None
```

Save config back to the file it was loaded from

If you want to save to a different file, use :func:`write_yaml`.


<a id="lauschkiste.cfghandler.ConfigHandler.load"></a>

#### load

```python
def load(filename: str) -> None
```

Load YAML config file into memory


<a id="lauschkiste.cfghandler.get_handler"></a>

#### get\_handler

```python
def get_handler(name: str) -> ConfigHandler
```

Get a configuration data handler with the specified name, creating it

if it doesn't yet exit. If created, it is always created empty.

This is the main entry point for obtaining an configuration handler

**Arguments**:

- `name`: Name of the config handler

**Returns**:

`ConfigHandler`: The configuration data handler for *name*

<a id="lauschkiste.cfghandler.load_yaml"></a>

#### load\_yaml

```python
def load_yaml(cfg: ConfigHandler, filename: str) -> None
```

Load a yaml file into a ConfigHandler

**Arguments**:

- `cfg`: ConfigHandler instance
- `filename`: filename to yaml file

**Returns**:

None

<a id="lauschkiste.cfghandler.ensure_default_config"></a>

#### ensure\_default\_config

```python
def ensure_default_config(filename: str, template: str) -> None
```

Create `filename` from `template` if it doesn't exist yet (creating parent directories as

needed). Lets a fresh checkout/install start with sensible defaults instead of requiring a
separate install step to have copied the template first.

**Arguments**:

- `filename`: path the config file is expected/wanted at
- `template`: path to the default template to copy from if `filename` is missing

**Returns**:

None

<a id="lauschkiste.cfghandler.write_yaml"></a>

#### write\_yaml

```python
def write_yaml(cfg: ConfigHandler,
               filename: str,
               only_if_changed: bool = False,
               *args,
               **kwargs) -> None
```

Writes ConfigHandler data to yaml file / sys.stdout

**Arguments**:

- `cfg`: ConfigHandler instance
- `filename`: filename to output file. If *sys.stdout*, output is written to console
- `only_if_changed`: Write file only, if ConfigHandler.is_modified()
- `args`: passed on to yaml.dump(...)
- `kwargs`: passed on to yaml.dump(...)

**Returns**:

None

<a id="lauschkiste.timers"></a>

# lauschkiste.timers

The timers core module: named countdowns that run an action when they expire.

Timers are configured under ``timers:``; each runs an action (``action``/``args``) after
``default_timeout_sec`` unless started with another duration. A timer whose action is not available
(e.g. its plugin is disabled) is listed, but can't be started.


<a id="lauschkiste.timers.Timers"></a>

## Timers Objects

```python
class Timers(CoreModule)
```

Countdown timers that run an action when they expire.


<a id="lauschkiste.timers.Timers.list_timers"></a>

#### list\_timers

```python
@query(path='')
def list_timers() -> List[TimerState]
```

All timers with their state.


<a id="lauschkiste.timers.Timers.start_timer"></a>

#### start\_timer

```python
@action(name='start', path='/start')
def start_timer(timer: str,
                wait_seconds: Optional[float] = None) -> TimerState
```

Start (or restart) a timer; ``wait_seconds`` defaults to the timer's configured timeout.


<a id="lauschkiste.timers.Timers.cancel"></a>

#### cancel

```python
@action(path='/cancel')
def cancel(timer: str) -> TimerState
```

Cancel a running timer.


<a id="lauschkiste.timers.Timers.toggle"></a>

#### toggle

```python
@action(path='/toggle')
def toggle(timer: str, wait_seconds: Optional[float] = None) -> TimerState
```

Start the timer if it is not running, cancel it otherwise.


<a id="lauschkiste.audio_output"></a>

# lauschkiste.audio\_output

PCM output through sounddevice/PortAudio, shared by the local_audio backend and the jingle.


<a id="lauschkiste.audio_output.volume_gain"></a>

#### volume\_gain

```python
def volume_gain(volume: int) -> float
```

Gain of a 0-100 volume setting. Cubic like PulseAudio's, so equal steps of the slider sound about

equally loud: 50 % is -18 dB, not -6 dB as a linear gain would be.


<a id="lauschkiste.audio_output.scale_gain"></a>

#### scale\_gain

```python
def scale_gain(data: bytes, gain: float) -> bytes
```

Scale packed s16 PCM by ``gain``. No-op at full gain (the common case).


<a id="lauschkiste.audio_output.scale_volume"></a>

#### scale\_volume

```python
def scale_volume(data: bytes, volume: int) -> bytes
```

Scale packed s16 PCM linearly by volume (0-100), e.g. a sound relative to the current output volume.


<a id="lauschkiste.audio_output.AudioSink"></a>

## AudioSink Objects

```python
class AudioSink()
```

What a decoded track is written to. Exists so tests don't need a real audio device.


<a id="lauschkiste.audio_output.AudioSink.close"></a>

#### close

```python
def close(discard: bool = False) -> float
```

Stop the output; ``discard`` drops what is still buffered. Returns the dropped seconds.


<a id="lauschkiste.audio_output.PortAudioSink"></a>

## PortAudioSink Objects

```python
class PortAudioSink(AudioSink)
```

Real output via sounddevice/PortAudio. Falls back to silent (no-op) if no device is

available -- e.g. the no-audio docker dev stack, or a CI box -- rather than raising and
killing the daemon.

The stream starts once ``PREFILL_SECONDS`` of audio are decoded, so the slow start of a track
(opening and probing the file) doesn't empty the device buffer right away.


<a id="lauschkiste.audio_output.PortAudioSink.LATENCY"></a>

#### LATENCY

A larger device buffer means fewer wake-ups: on a Pi Zero 0.3 s needs half the CPU of the default 35 ms


<a id="lauschkiste.audio_output.PortAudioSink.CHUNK_SECONDS"></a>

#### CHUNK\_SECONDS

Writes are collected to this length: fewer calls through PortAudio and ALSA


<a id="lauschkiste.audio_output.PortAudioSink.LEAD_IN_SECONDS"></a>

#### LEAD\_IN\_SECONDS

Amplifiers like the MAX98357A thump when the clock starts or stops with the signal. So the stream

starts with silence, the first audio fades in, and it ends with silence.


<a id="lauschkiste.audio_output.play_file"></a>

#### play\_file

```python
def play_file(path: str,
              volume: int = 100,
              sink=None,
              should_stop=lambda: False) -> None
```

Decode ``path`` and play it to the end (or until ``should_stop()``), blocking.


<a id="lauschkiste.core_modules"></a>

# lauschkiste.core\_modules

The core modules the daemon always starts. Order is irrelevant, ``requires`` decides.


<a id="lauschkiste.statefile"></a>

# lauschkiste.statefile

Small state files of core modules (JSON or YAML), written atomically.


<a id="lauschkiste.statefile.write_text"></a>

#### write\_text

```python
def write_text(path: Path, text: str) -> None
```

Write ``text`` via a temporary file and rename it, so a crash never leaves a truncated file.


<a id="lauschkiste.input_devices"></a>

# lauschkiste.input\_devices

The input core module: keys of evdev input devices (USB buttons, keyboards, headset buttons) run actions.

Configured under ``input:``::

    input:
      media_keys: false          # play/pause/next/volume keys of any device (e.g. a Bluetooth headset)
      devices:
        joystick:
          device_name: DragonRise Inc.   Generic   USB
          exact: false           # substring match of the device name
          keys:
            BTN_TRIGGER: {action: player.toggle}
            297: {action: player.prev}


<a id="lauschkiste.input_devices.Evdev"></a>

## Evdev Objects

```python
class Evdev()
```

Access to the evdev library; replaced in tests.


<a id="lauschkiste.input_devices.Evdev.key_downs"></a>

#### key\_downs

```python
def key_downs(device, stop: threading.Event)
```

Yield key codes pressed on ``device`` until ``stop`` is set; raises OSError on disconnect.


<a id="lauschkiste.input_devices.InputDevices"></a>

## InputDevices Objects

```python
class InputDevices(CoreModule)
```

Keys of input devices run actions.


<a id="lauschkiste.input_devices.InputDevices.available_devices"></a>

#### available\_devices

```python
@query(path='/available')
def available_devices() -> List[Choice]
```

Names of the input devices connected right now, for configuring keys.


<a id="lauschkiste.input_devices.InputDevices.list_devices"></a>

#### list\_devices

```python
@query(path='/devices')
def list_devices() -> List[DeviceState]
```

Configured input devices and whether they are connected.


<a id="lauschkiste.multitimer"></a>

# lauschkiste.multitimer

Threaded one-shot and fixed-delay periodic timers.


<a id="lauschkiste.multitimer.MultiTimer"></a>

## MultiTimer Objects

```python
class MultiTimer(threading.Thread)
```

Execute a callback after each fixed-delay interval.

Limited timers count iterations down from ``iterations - 1`` to zero.
Negative iteration counts repeat until cancellation.


<a id="lauschkiste.multitimer.MultiTimer.cancel"></a>

#### cancel

```python
def cancel()
```

Stop the timer and wake its worker.


<a id="lauschkiste.multitimer.MultiTimer.trigger"></a>

#### trigger

```python
def trigger()
```

Trigger the next callback immediately.


<a id="lauschkiste.multitimer.MultiTimer.run"></a>

#### run

```python
def run()
```

Run until all iterations complete, cancellation, or callback failure.


<a id="lauschkiste.multitimer.GenericTimerClass"></a>

## GenericTimerClass Objects

```python
class GenericTimerClass()
```

A race-safe, single-execution timer. ``on_change(state)`` is called on every state change.


<a id="lauschkiste.multitimer.GenericTimerClass.start"></a>

#### start

```python
def start(wait_seconds: Optional[float] = None, restart: bool = True)
```

Start the timer, atomically replacing an active generation by default.


<a id="lauschkiste.multitimer.GenericTimerClass.cancel"></a>

#### cancel

```python
def cancel()
```

Cancel the active generation.


<a id="lauschkiste.multitimer.GenericTimerClass.cancel_generation"></a>

#### cancel\_generation

```python
def cancel_generation(worker)
```

Cancel one worker without affecting a newer generation.


<a id="lauschkiste.multitimer.GenericTimerClass.toggle"></a>

#### toggle

```python
def toggle()
```

Toggle between active and disabled states.


<a id="lauschkiste.multitimer.GenericTimerClass.trigger"></a>

#### trigger

```python
def trigger()
```

Trigger the active generation immediately.


<a id="lauschkiste.multitimer.GenericTimerClass.is_alive"></a>

#### is\_alive

```python
def is_alive() -> bool
```

Return whether a timer generation is logically active.


<a id="lauschkiste.multitimer.GenericTimerClass.get_timeout"></a>

#### get\_timeout

```python
def get_timeout() -> float
```

Return the configured timeout in seconds.


<a id="lauschkiste.multitimer.GenericTimerClass.set_timeout"></a>

#### set\_timeout

```python
def set_timeout(wait_seconds: float) -> float
```

Set the timeout, atomically replacing an active generation.


<a id="lauschkiste.multitimer.GenericTimerClass.publish"></a>

#### publish

```python
def publish()
```

Publish the current timer state.


<a id="lauschkiste.multitimer.GenericTimerClass.get_state"></a>

#### get\_state

```python
def get_state() -> Dict[str, Any]
```

Return the timer state.


<a id="lauschkiste.multitimer.GenericTimerClass.close"></a>

#### close

```python
def close()
```

Permanently close this timer and join all active workers.


<a id="lauschkiste.multitimer.GenericEndlessTimerClass"></a>

## GenericEndlessTimerClass Objects

```python
class GenericEndlessTimerClass(GenericTimerClass)
```

A fixed-delay timer that repeats until cancellation.


<a id="lauschkiste.multitimer.GenericEndlessTimerClass.get_state"></a>

#### get\_state

```python
def get_state() -> Dict[str, Any]
```

Return the periodic timer state.


<a id="lauschkiste.paths"></a>

# lauschkiste.paths

Where Lauschkiste keeps its data (``LAUSCHKISTE_HOME``) and its packaged resources.

All runtime data lives below one directory::

    $LAUSCHKISTE_HOME/settings/      configuration, card database, library index, status files
    $LAUSCHKISTE_HOME/library/       the library: music/, audiobooks/
    $LAUSCHKISTE_HOME/logs/  cache/  playlists/

Relative paths in the configuration are resolved against ``LAUSCHKISTE_HOME``.


<a id="lauschkiste.paths.home"></a>

#### home

```python
def home() -> Path
```

The home: set explicitly, else ``$LAUSCHKISTE_HOME``, else ``$XDG_DATA_HOME/lauschkiste``.


<a id="lauschkiste.paths.set_home"></a>

#### set\_home

```python
def set_home(path: Union[str, Path, None]) -> None
```

Use ``path`` as home (None: determine it again from the environment).


<a id="lauschkiste.paths.resolve"></a>

#### resolve

```python
def resolve(value: Union[str, Path]) -> Path
```

A configured path: absolute or ``~`` as given, relative ones below the home.


<a id="lauschkiste.paths.library_dir"></a>

#### library\_dir

```python
def library_dir(configured: Union[str, Path, None] = None) -> Path
```

The library (``library.path``, by default ``library`` in the home).


<a id="lauschkiste.paths.resource"></a>

#### resource

```python
def resource(*parts: str) -> Path
```

A file shipped with the package (default settings, sounds, service templates).


<a id="lauschkiste.daemon"></a>

# lauschkiste.daemon

<a id="lauschkiste.daemon.DEFAULT_CONFIG_TEMPLATE"></a>

#### DEFAULT\_CONFIG\_TEMPLATE

Template a missing configuration_file is created from on first run (see Daemon.__init__).


<a id="lauschkiste.daemon.shutdown_signal"></a>

#### shutdown\_signal

```python
def shutdown_signal() -> Optional[int]
```

The signal that started the shutdown (e.g. ``signal.SIGINT`` for Ctrl-C), None before.


<a id="lauschkiste.daemon.log_active_threads"></a>

#### log\_active\_threads

```python
@atexit.register
def log_active_threads()
```

This functions is registered with atexit very early, meaning it will be run very late. It is the best guess to

evaluate which Threads are still running (and probably shouldn't be)

This function is registered before all the components and their dependencies are loaded


<a id="lauschkiste.daemon.Daemon"></a>

## Daemon Objects

```python
class Daemon()
```

<a id="lauschkiste.daemon.Daemon.signal_handler"></a>

#### signal\_handler

```python
def signal_handler(esignal, frame)
```

Signal handler for orderly shutdown

On first Ctrl-C (or SIGTERM) orderly shutdown procedure is embarked upon. It gets allocated a time-out!
On third Ctrl-C (or SIGTERM), this is interrupted and there will be a hard exit!


<a id="lauschkiste.misc.simplecolors"></a>

# lauschkiste.misc.simplecolors

Zero 3rd-party dependency module to add colors to unix terminal output

Yes, there are modules out there to do the same and they have more features.
However, this is low-complexity and has zero dependencies


<a id="lauschkiste.misc.simplecolors.Colors"></a>

## Colors Objects

```python
class Colors()
```

Container class for all the colors as constants


<a id="lauschkiste.misc.simplecolors.resolve"></a>

#### resolve

```python
def resolve(color_name: str)
```

Resolve a color name into the respective color constant

**Arguments**:

- `color_name`: Name of the color

**Returns**:

color constant

<a id="lauschkiste.misc.simplecolors.print"></a>

#### print

```python
def print(color: Colors,
          *values,
          sep=' ',
          end='\n',
          file=sys.stdout,
          flush=False)
```

Drop-in replacement for print with color choice and auto color reset for convenience

Use just as a regular print function, but with first parameter as color


<a id="lauschkiste.misc"></a>

# lauschkiste.misc

<a id="lauschkiste.misc.recursive_chmod"></a>

#### recursive\_chmod

```python
def recursive_chmod(path, mode_files, mode_dirs)
```

Recursively change folder and file permissions

mode_files/mode dirs can be given in octal notation e.g. 0o777
flags from the stats module.

Reference: https://docs.python.org/3/library/os.html#os.chmod


<a id="lauschkiste.misc.flatten"></a>

#### flatten

```python
def flatten(iterable)
```

Flatten all levels of hierarchy in nested iterables


<a id="lauschkiste.misc.getattr_hierarchical"></a>

#### getattr\_hierarchical

```python
def getattr_hierarchical(obj: Any, name: str) -> Any
```

Like the builtin getattr, but descends though the hierarchy levels


<a id="lauschkiste.misc.inputminus"></a>

# lauschkiste.misc.inputminus

Zero 3rd-party dependency module for user prompting

Yes, there are modules out there to do the same and they have more features.
However, this is low-complexity and has zero dependencies


<a id="lauschkiste.misc.inputminus.input_int"></a>

#### input\_int

```python
def input_int(prompt,
              blank=None,
              min=None,
              max=None,
              prompt_color=None,
              prompt_hint=False) -> int
```

Request an integer input from user

**Arguments**:

- `prompt`: The prompt to display
- `blank`: Value to return when user just hits enter. Leave at None, if blank is invalid
- `min`: Minimum valid integer value (None disables this check)
- `max`: Maximum valid integer value (None disables this check)
- `prompt_color`: Color of the prompt. Color will be reset at end of prompt
- `prompt_hint`: Append a 'hint' with [min...max, default=xx] to end of prompt

**Returns**:

integer value read from user input

<a id="lauschkiste.misc.inputminus.input_yesno"></a>

#### input\_yesno

```python
def input_yesno(prompt,
                blank=None,
                prompt_color=None,
                prompt_hint=False) -> bool
```

Request a yes / no choice from user

Accepts multiple input for true/false and is case insensitive

**Arguments**:

- `prompt`: The prompt to display
- `blank`: Value to return when user just hits enter. Leave at None, if blank is invalid
- `prompt_color`: Color of the prompt. Color will be reset at end of prompt
- `prompt_hint`: Append a 'hint' with [y/n] to end of prompt. Default choice will be capitalized

**Returns**:

boolean value read from user input

<a id="lauschkiste.misc.loggingext"></a>

# lauschkiste.misc.loggingext

## Logger

We use a hierarchical Logger structure based on pythons logging module. It can be finely configured with a yaml file.

The top-level logger is called 'lauschkiste'. In any module you may simple create a child-logger at any hierarchy
level below 'lauschkiste'. It will inherit settings from it's parent logger unless otherwise configured in the yaml file.
Hierarchy separator is the '.'. If the logger already exits, getLogger will return a reference to the same, else it will be
created on the spot.

Example: How to get logger and log away at your heart's content:

    >>> import logging
    >>> logger = logging.getLogger('lauschkiste.awesome_module')
    >>> logger.info('Started general awesomeness aura')

Example: YAML snippet, setting WARNING as default level everywhere and DEBUG for lauschkiste.awesome_module:

    loggers:
      lauschkiste:
        level: WARNING
        handlers: [console, debug_file_handler, error_file_handler]
        propagate: no
      lauschkiste.awesome_module:
        level: DEBUG


> [!NOTE]
> The name (and hierarchy path) of the logger can be arbitrary and must not necessarily match the module name (still makes
> sense).
> There can be multiple loggers per module, e.g. for special classes, to further control the amount of log output


<a id="lauschkiste.misc.loggingext.ColorFilter"></a>

## ColorFilter Objects

```python
class ColorFilter(logging.Filter)
```

This filter adds colors to the logger

It adds all colors from simplecolors by using the color name as new keyword,
i.e. use %(colorname)c or {colorname} in the formatter string

It also adds the keyword {levelnameColored} which is an auto-colored drop-in replacement
for the levelname depending on severity.

Don't forget to {reset} the color settings at the end of the string.


<a id="lauschkiste.misc.loggingext.ColorFilter.__init__"></a>

#### \_\_init\_\_

```python
def __init__(enable=True, color_levelname=True)
```

**Arguments**:

- `enable`: Enable the coloring
- `color_levelname`: Enable auto-coloring when using the levelname keyword

<a id="lauschkiste.misc.loggingext.PubStream"></a>

## PubStream Objects

```python
class PubStream()
```

Stream handler wrapper around the publisher for logging.StreamHandler

Allows logging to send all log information (based on logging configuration)
to the Publisher.

> [!CAUTION]
> This can lead to recursions!
> Recursions come up when
> * Publish.send / EventBus.publish also emits logs, which cause a another send, which emits a log,
> which causes a send, ..... `lauschkiste.publishing.bus.EventBus` guards against this (caps it at one
> extra level instead of recursing indefinitely), but still avoid triggering it needlessly.
> * Publisher initialization emits logs, which need a Publisher instance to send logs

> [!IMPORTANT]
> To avoid endless recursions: The creation of a Publisher MUST NOT generate any log messages! Nor any of the
> functions in the send-function stack!


<a id="lauschkiste.misc.loggingext.PubStreamHandler"></a>

## PubStreamHandler Objects

```python
class PubStreamHandler(logging.StreamHandler)
```

Wrapper for logging.StreamHandler with stream = PubStream

This serves one purpose: In logger.yaml custom handlers
can be configured (which are automatically instantiated).
Using this Handler, we can output to PubStream whithout
support code to instantiate PubStream keeping this file generic


<a id="lauschkiste.time_limits"></a>

# lauschkiste.time\_limits

The time_limits core module: quiet hours and a daily listening limit.

It is off until switched on in the settings::

    time_limits:
      enabled: true
      quiet_hours:
        bedtime: {start: '19:30', end: '07:00', days: every day}
      daily_limit_minutes: 120

Playback that starts in quiet hours is stopped at once. The time something plays is counted per day; when the
limit is reached the sound fades out and the player stops, and playback stays blocked until the next day.
The action ``time_limits.allow`` adds time for today (and lifts quiet hours for that time); put it on a card
for the parents.


<a id="lauschkiste.time_limits.SETTLE_SEC"></a>

#### SETTLE\_SEC

after stopping the player the rules are not applied again for this long (the status needs a moment to follow)


<a id="lauschkiste.time_limits.TimeLimitStatus"></a>

## TimeLimitStatus Objects

```python
class TimeLimitStatus(BaseModel)
```

<a id="lauschkiste.time_limits.TimeLimitStatus.enabled"></a>

#### enabled

false while the time limits are switched off; nothing is blocked or counted then


<a id="lauschkiste.time_limits.TimeLimitStatus.clock_ok"></a>

#### clock\_ok

false when the system clock is not synchronized: quiet hours are not enforced then


<a id="lauschkiste.time_limits.TimeLimitStatus.reason"></a>

#### reason

'quiet' (quiet hours) or 'limit' (the day's time is used up)


<a id="lauschkiste.time_limits.TimeLimitStatus.until"></a>

#### until

for quiet hours, when they end ("07:00")


<a id="lauschkiste.time_limits.clock_synchronized"></a>

#### clock\_synchronized

```python
def clock_synchronized() -> Optional[bool]
```

Whether the clock is synchronized (None if the system cannot tell).


<a id="lauschkiste.time_limits.TimeLimits"></a>

## TimeLimits Objects

```python
class TimeLimits(CoreModule)
```

Quiet hours and a daily listening limit (off until switched on).


<a id="lauschkiste.time_limits.TimeLimits.evaluate"></a>

#### evaluate

```python
def evaluate() -> TimeLimitStatus
```

Where the day stands (called by the tick, the status query and the actions).


<a id="lauschkiste.time_limits.TimeLimits.status"></a>

#### status

```python
@query(path='/status')
def status() -> TimeLimitStatus
```

Quiet hours, the time used today and what is left.


<a id="lauschkiste.time_limits.TimeLimits.allow"></a>

#### allow

```python
@action()
def allow(minutes: int = 30) -> TimeLimitStatus
```

Add listening time for today; quiet hours are lifted for that long as well. Meant for parents (put it on a card).


<a id="lauschkiste.time_limits.TimeLimits.reset_today"></a>

#### reset\_today

```python
@action()
def reset_today() -> TimeLimitStatus
```

Count today's listening time from zero again.


<a id="lauschkiste.time_limits.rules"></a>

# lauschkiste.time\_limits.rules

The rules of the time limits, without clocks or threads: quiet hours and the allowance of a day.


<a id="lauschkiste.time_limits.rules.quiet_until"></a>

#### quiet\_until

```python
def quiet_until(ranges: Dict[str, Tuple[str, str, str]],
                now: datetime) -> Optional[datetime]
```

When the quiet hours that cover ``now`` end, or None. A range that runs past midnight belongs to the day it

starts on: 19:30-07:00 on weekdays covers Friday evening until Saturday morning.


<a id="lauschkiste.time_limits.rules.limit_seconds"></a>

#### limit\_seconds

```python
def limit_seconds(weekday_minutes: int, weekend_minutes: Optional[int],
                  now: datetime) -> Optional[int]
```

The listening time of the day in seconds; None for no limit.


<a id="lauschkiste.contract.secrets"></a>

# lauschkiste.contract.secrets

Secrets (API keys, passwords) of modules, kept apart from the main configuration.

They live in ``secrets.yaml`` next to the configuration file, readable for the user only, under the
same key path as the setting (``plugins.<name>.<key>``). Modules read them through ``ctx.config`` as
if they were ordinary settings; the main configuration, which people share and back up, never holds them.


<a id="lauschkiste.contract.secrets.SecretStore"></a>

## SecretStore Objects

```python
class SecretStore()
```

<a id="lauschkiste.contract.secrets.SecretStore.set"></a>

#### set

```python
def set(*keys: str, value: Any) -> None
```

Store a value and write the file; an empty value removes it.


<a id="lauschkiste.contract.interfaces"></a>

# lauschkiste.contract.interfaces

Interface snapshots of modules and the framework contract, and the rules for version bumps.

A snapshot is a JSON description of everything another module or plugin can rely on. Comparing
the stored snapshot with the current one tells whether a change is compatible (minor bump) or
breaking (major bump). See documentation/developers/core-and-plugins.md, "Versioning".


<a id="lauschkiste.contract.interfaces.format_signature"></a>

#### format\_signature

```python
def format_signature(func) -> str
```

``str(inspect.signature(func))``, but rendering unions the same way on every Python version.


<a id="lauschkiste.contract.declarations"></a>

# lauschkiste.contract.declarations

Declarations a module uses to describe its interface: operations, events, extension points.


<a id="lauschkiste.contract.declarations.OperationSpec"></a>

## OperationSpec Objects

```python
@dataclass(frozen=True)
class OperationSpec()
```

<a id="lauschkiste.contract.declarations.OperationSpec.kind"></a>

#### kind

'action' | 'query'


<a id="lauschkiste.contract.declarations.action"></a>

#### action

```python
def action(func: Optional[Callable] = None,
           *,
           method: str = 'POST',
           path: Optional[str] = None,
           exclusive: bool = True,
           name: Optional[str] = None,
           status_code: Optional[int] = None)
```

Declare a state-changing operation: REST route, card action and in-process call.

``name`` overrides the operation name (default: the method name), e.g. where the method name
would clash with the lifecycle methods ``start``/``stop``/``ready``. ``status_code`` replaces
the default HTTP status of a successful call (200, or 204 without a result).


<a id="lauschkiste.contract.declarations.query"></a>

#### query

```python
def query(func: Optional[Callable] = None,
          *,
          path: Optional[str] = None,
          exclusive: bool = True,
          name: Optional[str] = None)
```

Declare a read-only operation: GET route and in-process call, not card-triggerable.


<a id="lauschkiste.contract.declarations.EventSpec"></a>

## EventSpec Objects

```python
class EventSpec()
```

A declared event. Published through ``ctx.publish(spec, payload)`` as ``<module>.<name>``.


<a id="lauschkiste.contract.declarations.ExtensionPoint"></a>

## ExtensionPoint Objects

```python
class ExtensionPoint()
```

Named implementations of a protocol, registered by other modules.


<a id="lauschkiste.contract.declarations.ExtensionPoint.on_register"></a>

#### on\_register

```python
def on_register(listener: Callable[[str, Any], None]) -> None
```

Call ``listener(key, implementation)`` for every current and future registration.


<a id="lauschkiste.contract.declarations.ExtensionPointSpec"></a>

## ExtensionPointSpec Objects

```python
class ExtensionPointSpec()
```

Class-level declaration of an extension point; each module instance gets its own registry.


<a id="lauschkiste.contract.declarations.Operation"></a>

## Operation Objects

```python
class Operation()
```

An operation of a module class with its argument model and return type.


<a id="lauschkiste.contract.declarations.Operation.validate_args"></a>

#### validate\_args

```python
def validate_args(args: Optional[dict]) -> dict
```

Validate a mapping of arguments; return the coerced keyword arguments.


<a id="lauschkiste.contract.catalog"></a>

# lauschkiste.contract.catalog

Card-triggerable actions of all started modules, addressed by ``<module>.<action>``.


<a id="lauschkiste.contract.catalog.ActionCatalog"></a>

## ActionCatalog Objects

```python
class ActionCatalog()
```

<a id="lauschkiste.contract.catalog.ActionCatalog.validate"></a>

#### validate

```python
def validate(action_id: str, args: Optional[dict] = None) -> Dict[str, Any]
```

Check that ``action_id`` exists and ``args`` fit its signature. Returns coerced args.


<a id="lauschkiste.contract.catalog.ActionCatalog.bind"></a>

#### bind

```python
def bind(entry: Any, where: str,
         log: logging.Logger) -> Optional[Callable[[], Any]]
```

A callable running a configured action (``{'action': <id>, 'args': {...}}``), or None

(logged) if the entry is invalid.


<a id="lauschkiste.contract.context"></a>

# lauschkiste.contract.context

What a module sees of the rest of the system.


<a id="lauschkiste.contract.context.ModuleConfig"></a>

## ModuleConfig Objects

```python
class ModuleConfig()
```

A module's own section of the main config (``<name>`` for core, ``plugins.<name>`` for plugins).


<a id="lauschkiste.contract.context.ModuleProxy"></a>

## ModuleProxy Objects

```python
class ModuleProxy()
```

The contract surface of another module: its operations and extension points.


<a id="lauschkiste.contract.context.Context"></a>

## Context Objects

```python
class Context()
```

<a id="lauschkiste.contract.context.Context.lock"></a>

#### lock

```python
@property
def lock()
```

The module's own lock, for work outside operations (e.g. background threads).

A no-op context manager for ``concurrency = 'threadsafe'`` modules.


<a id="lauschkiste.contract.context.Context.subscribe"></a>

#### subscribe

```python
def subscribe(topic_prefix: str, callback: Callable[[str, Optional[Any]],
                                                    None]) -> None
```

Call ``callback(topic, payload)`` for every event under ``topic_prefix``; payload None = revoked.


<a id="lauschkiste.contract.routes"></a>

# lauschkiste.contract.routes

FastAPI routes generated from module operations, plus ``GET /api/v1/modules``.


<a id="lauschkiste.contract.routes.response_adapter"></a>

#### response\_adapter

```python
def response_adapter(op: Operation) -> TypeAdapter
```

Validates and serializes the return value; built on first use, which keeps start-up fast on small boards.


<a id="lauschkiste.contract.routes.add_response_schemas"></a>

#### add\_response\_schemas

```python
def add_response_schemas(schema: Dict[str, Any], operations) -> Dict[str, Any]
```

Add the operations' return types to an OpenAPI ``schema`` (FastAPI doesn't know them).


<a id="lauschkiste.contract.routes.add_settings_routes"></a>

#### add\_settings\_routes

```python
def add_settings_routes(router: APIRouter, manager: ModuleManager,
                        executor) -> None
```

Settings of the modules and whether a restart is pending.


<a id="lauschkiste.contract.routes.add_plugin_routes"></a>

#### add\_plugin\_routes

```python
def add_plugin_routes(router: APIRouter, manager: ModuleManager,
                      blocking) -> None
```

Installed plugins: list, enable or disable, install missing extras.


<a id="lauschkiste.contract.manager"></a>

# lauschkiste.contract.manager

Discovers, orders, starts and stops core modules and enabled plugins.


<a id="lauschkiste.contract.manager.discover_plugins"></a>

#### discover\_plugins

```python
def discover_plugins() -> Dict[str, Callable[[], type]]
```

Installed plugins by entry-point name. Loading (importing) happens only when enabled.


<a id="lauschkiste.contract.manager.ModuleHandle"></a>

## ModuleHandle Objects

```python
class ModuleHandle()
```

A started (or starting) module instance plus its lock and context.


<a id="lauschkiste.contract.manager.ModuleManager"></a>

## ModuleManager Objects

```python
class ModuleManager()
```

<a id="lauschkiste.contract.manager.ModuleManager.__init__"></a>

#### \_\_init\_\_

```python
def __init__(core_modules: Sequence[Type[CoreModule]],
             cfg,
             bus,
             *,
             plugins: Optional[Dict[str, Callable[[], type]]] = None,
             strict: Optional[bool] = None)
```

**Arguments**:

- `core_modules`: core module classes (order doesn't matter, ``requires`` decides)
- `cfg`: the main config handler; plugins are enabled under its ``plugins`` key
- `bus`: the event bus
- `plugins`: installed plugins by name (default: entry points of ``lauschkiste.plugins``)
- `strict`: raise instead of log on invalid events (default: ``$LAUSCHKISTE_STRICT``)

<a id="lauschkiste.contract.module"></a>

# lauschkiste.contract.module

Base classes for core modules and plugins.


<a id="lauschkiste.contract.module.Module"></a>

## Module Objects

```python
class Module()
```

Common base of :class:`CoreModule` and :class:`Plugin`. Not subclassed directly.


<a id="lauschkiste.contract.module.Module.concurrency"></a>

#### concurrency

'serialized': every operation runs under a per-module lock. 'threadsafe': no lock.


<a id="lauschkiste.contract.module.Module.settings"></a>

#### settings

The settings of the module's config section, editable through the web app. Field titles and

descriptions are shown; ``Field(json_schema_extra={'widget': 'action'})`` marks an action entry.


<a id="lauschkiste.contract.module.Module.ready"></a>

#### ready

```python
def ready() -> None
```

Called once every module has started, in start order. All actions are available now.


<a id="lauschkiste.contract.module.Module.settings_changed"></a>

#### settings\_changed

```python
def settings_changed(changed: Dict[str, Any]) -> bool
```

Settings were changed through the web app (already in ``ctx.config``). Return True if

they take effect right away, False if Lauschkiste must restart for them.


<a id="lauschkiste.contract.module.Module.extra_routes"></a>

#### extra\_routes

```python
def extra_routes(router) -> None
```

Escape hatch for routes the declarations can't express (e.g. streaming uploads).

Receives a FastAPI ``APIRouter``; paths should live under ``/api/v1/<name>``.


<a id="lauschkiste.contract.module.CoreModule"></a>

## CoreModule Objects

```python
class CoreModule(Module)
```

Always shipped, always running part of Lauschkiste.


<a id="lauschkiste.contract.module.Plugin"></a>

## Plugin Objects

```python
class Plugin(Module)
```

Separately installed, opt-in module. Declares which framework contract it targets.


<a id="lauschkiste.contract.module.Plugin.extras"></a>

#### extras

Extras of the plugin's own package it needs (installed by `lauschctl plugin enable --with-extras`)


<a id="lauschkiste.contract.module.Plugin.title"></a>

#### title

The name shown in the plugin list when no translation exists (default: the plugin's name made readable)


<a id="lauschkiste.contract.module.Plugin.provides"></a>

#### provides

Capabilities it offers other plugins, e.g. ``('board', 'gpio', 'i2c')``; only one plugin may provide 'board'


<a id="lauschkiste.contract.module.Plugin.needs"></a>

#### needs

Capabilities an enabled plugin must provide, e.g. ``('i2c',)``


<a id="lauschkiste.contract.module.Plugin.detect"></a>

#### detect

```python
@classmethod
def detect(cls, read: Callable[[str], Optional[str]]) -> Optional[str]
```

The hardware of this plugin found on this machine (e.g. a board model), or None.

``read(path)`` returns a file's text or None.


<a id="lauschkiste.contract.version"></a>

# lauschkiste.contract.version

<a id="lauschkiste.contract.version.CONTRACT_VERSION"></a>

#### CONTRACT\_VERSION

Version of the framework contract (Module/CoreModule/Plugin, declarations, Context, lifecycle).

Major bump on breaking changes, minor bump on additions. Checked by test/contract snapshots.


<a id="lauschkiste.contract"></a>

# lauschkiste.contract

Contract shared by core modules and plugins. See documentation/developers/core-and-plugins.md.


<a id="lauschkiste.contract.snapshots"></a>

# lauschkiste.contract.snapshots

Check or update the stored interface snapshots of the framework, core modules and bundled plugins.

uv run python -m lauschkiste.contract.snapshots            # check (what CI runs via pytest)
uv run python -m lauschkiste.contract.snapshots --update   # write snapshots after a version bump


<a id="lauschkiste.contract.snapshots.check_target"></a>

#### check\_target

```python
def check_target(target: Target) -> Optional[str]
```

Return a problem description, or None when the stored snapshot matches.


<a id="lauschkiste.contract.settings"></a>

# lauschkiste.contract.settings

Module settings: read, validate and store a module's config section through its ``settings`` model.


<a id="lauschkiste.contract.settings.ActionEntry"></a>

## ActionEntry Objects

```python
class ActionEntry(BaseModel)
```

An action with its arguments, as on cards (shown as an action picker in the web app).


<a id="lauschkiste.contract.settings.storage"></a>

#### storage

```python
def storage(handle, cfg) -> tuple
```

(config handler, key path) of a module's settings: its section of the main config, unless the

module keeps them elsewhere (``settings_storage()``).


<a id="lauschkiste.contract.settings.secret_fields"></a>

#### secret\_fields

```python
def secret_fields(model: type) -> Set[str]
```

Fields marked ``json_schema_extra={'secret': True}``: shown as password fields, never sent to the client.


<a id="lauschkiste.contract.settings.current_values"></a>

#### current\_values

```python
def current_values(model: type, section: Any) -> Dict[str, Any]
```

The settings from a config section; invalid or unknown entries fall back to the defaults.


<a id="lauschkiste.contract.settings.SettingsStore"></a>

## SettingsStore Objects

```python
class SettingsStore()
```

Settings of the started modules, written to the main config file right away.


<a id="lauschkiste.contract.errors"></a>

# lauschkiste.contract.errors

<a id="lauschkiste.contract.errors.ContractError"></a>

## ContractError Objects

```python
class ContractError(Exception)
```

A module violates the contract (declaration, dependency or version problem).


<a id="lauschkiste.contract.errors.OperationError"></a>

## OperationError Objects

```python
class OperationError(Exception)
```

Raised by an operation to report a client error with an HTTP status and error code.


<a id="lauschkiste.contract.errors.ActionError"></a>

## ActionError Objects

```python
class ActionError(Exception)
```

An action id or its arguments are invalid.


<a id="lauschkiste.contract.plugins"></a>

# lauschkiste.contract.plugins

Installed plugins: their extras, whether those are installed, and enabling them in the config.


<a id="lauschkiste.contract.plugins.readable"></a>

#### readable

```python
def readable(name: str) -> str
```

``podcast_directories`` -> ``Podcast directories``: what is shown for a plugin nobody named.


<a id="lauschkiste.contract.plugins.package_info"></a>

#### package\_info

```python
def package_info(dist) -> Dict[str, Optional[str]]
```

What the package says about itself (author, license, project addresses), for a plugin list or manager.


<a id="lauschkiste.contract.plugins.installed"></a>

#### installed

```python
def installed() -> Dict[str, Any]
```

Entry points of the installed plugins by name.


<a id="lauschkiste.contract.plugins.load"></a>

#### load

```python
def load(ep)
```

(plugin class, None) or (None, reason it can't be imported).


<a id="lauschkiste.contract.plugins.taken_by"></a>

#### taken\_by

```python
def taken_by(cls, others: Iterable[type]) -> Optional[str]
```

The other plugin already providing an exclusive capability of ``cls`` (e.g. the board).


<a id="lauschkiste.contract.plugins.missing_needs"></a>

#### missing\_needs

```python
def missing_needs(cls, others: Iterable[type]) -> List[str]
```

Capabilities ``cls`` needs that none of ``others`` provides.


<a id="lauschkiste.contract.plugins.blocker"></a>

#### blocker

```python
def blocker(cls, others: Iterable[type]) -> Optional[Dict[str, Any]]
```

Why ``cls`` can't run next to ``others``: ``{'taken_by': name}`` or ``{'missing': [...]}``.


<a id="lauschkiste.contract.plugins.why_not_enable"></a>

#### why\_not\_enable

```python
def why_not_enable(cfg, name: str) -> Optional[str]
```

Why the installed plugin ``name`` can't be enabled next to the enabled ones, None if it can.


<a id="lauschkiste.contract.plugins.detected_boards"></a>

#### detected\_boards

```python
def detected_boards(read=read_text) -> List[Dict[str, str]]
```

Installed board plugins whose board this machine is: ``[{'name', 'model'}]``.


<a id="lauschkiste.contract.plugins.plugin_extras"></a>

#### plugin\_extras

```python
def plugin_extras(name: str) -> List[str]
```

Requirements for the extras plugin ``name`` declares, e.g. ``['pkg[gpio]']``.


<a id="lauschkiste.contract.plugins.missing_extras"></a>

#### missing\_extras

```python
def missing_extras(name: str) -> List[str]
```

``plugin_extras(name)`` whose dependencies are not (all) installed in this environment.


<a id="lauschkiste.contract.plugins.install_command"></a>

#### install\_command

```python
def install_command(requirements: List[str]) -> List[str]
```

Install into the environment Lauschkiste runs in: uv (also from ~/.local/bin) or pip.


<a id="lauschkiste.contract.plugins.ExtrasInstaller"></a>

## ExtrasInstaller Objects

```python
class ExtrasInstaller()
```

Installs the missing extras of plugins in the background, one plugin at a time.


<a id="lauschkiste.contract.plugins.ExtrasInstaller.start"></a>

#### start

```python
def start(name: str) -> bool
```

Start installing; False if nothing is missing or an installation is running.


<a id="lauschkiste.contract.plugins.set_enabled"></a>

#### set\_enabled

```python
def set_enabled(cfg, name: str, on: bool) -> bool
```

Enable or disable ``name`` in the config (disabling drops its settings); True if it changed.


<a id="lauschkiste.contract.plugins.describe"></a>

#### describe

```python
def describe(
        cfg,
        manager=None,
        installer: Optional[ExtrasInstaller] = None) -> List[Dict[str, Any]]
```

Installed (and enabled but missing) plugins: package, summary, enabled, running, problem, missing extras.


<a id="lauschkiste.contract.plugins.translations"></a>

#### translations

```python
def translations(language: str) -> Dict[str, Any]
```

What the installed plugins ship for ``language``, as part of the web app's translation file.

``<package>/translations/<language>.json`` holds ``{"plugins": {"<plugin>": {"name": ..., "description": ...,
"fields": ...}}}`` for the plugins of the package, ``fields`` shaped like ``settings.fields.<plugin>``.


<a id="lauschkiste.system"></a>

# lauschkiste.system

The system core module: version, logs, system information and web app settings.


<a id="lauschkiste.system.cpu_temperature"></a>

#### cpu\_temperature

```python
def cpu_temperature() -> Optional[float]
```

CPU temperature in °C from the first thermal zone, None where there is none.


<a id="lauschkiste.system.ip_addresses"></a>

#### ip\_addresses

```python
def ip_addresses() -> List[str]
```

Non-loopback IPv4 addresses of this machine.


<a id="lauschkiste.system.own_unit"></a>

#### own\_unit

```python
def own_unit(cgroup: str = '/proc/self/cgroup') -> Optional[str]
```

The systemd service this process runs in (e.g. ``lauschkiste.service``), None outside one.


<a id="lauschkiste.system.System"></a>

## System Objects

```python
class System(CoreModule)
```

Version information, log files and web app settings.


<a id="lauschkiste.system.System.log"></a>

#### log

Published by lauschkiste.misc.loggingext.PubStreamHandler when configured in logger.yaml


<a id="lauschkiste.system.System.get_info"></a>

#### get\_info

```python
@query(path='/info')
def get_info() -> SystemInfo
```

Version, git state and start time of Lauschkiste.


<a id="lauschkiste.system.System.get_health"></a>

#### get\_health

```python
@query(path='/health')
def get_health() -> SystemHealth
```

CPU temperature (where available) and disk usage of the music library's file system.


<a id="lauschkiste.system.System.get_ip_addresses"></a>

#### get\_ip\_addresses

```python
@query(path='/ip-addresses')
def get_ip_addresses() -> IpAddresses
```

IPv4 addresses of this machine.


<a id="lauschkiste.system.System.say_my_ip"></a>

#### say\_my\_ip

```python
@action()
def say_my_ip() -> None
```

Speak the IP address (needs espeak).


<a id="lauschkiste.system.System.restart_service"></a>

#### restart\_service

```python
@action()
def restart_service() -> None
```

Restart the systemd user service Lauschkiste runs in.


<a id="lauschkiste.system.System.get_log"></a>

#### get\_log

```python
@query(path='/log')
def get_log(kind: Literal['debug', 'error'] = 'debug') -> str
```

Content of the debug or error log file of this run.


<a id="lauschkiste.system.System.get_app_settings"></a>

#### get\_app\_settings

```python
@query(path='/api/v1/settings')
def get_app_settings() -> AppSettings
```

Web app settings.


<a id="lauschkiste.system.System.set_app_settings"></a>

#### set\_app\_settings

```python
@action(method='PUT', path='/api/v1/settings')
def set_app_settings(settings: AppSettingsUpdate) -> None
```

Change web app settings; fields left out stay unchanged.


<a id="lauschkiste.system.System.noop"></a>

#### noop

```python
@action()
def noop(message: str = '') -> None
```

Do nothing (logs ``message`` as a warning if given).


<a id="lauschkiste.hardware"></a>

# lauschkiste.hardware

The hardware core module: the active board, which pins and buses are used by whom, and power.

Board-neutral: a board support plugin registers at ``hardware.boards`` and describes its pins and
interfaces; modules using pins or buses register at ``hardware.claims``. See
documentation/developers/hardware.md.


<a id="lauschkiste.hardware.Claim"></a>

## Claim Objects

```python
class Claim(BaseModel)
```

A resource (pin or interface) a module uses; buses like I²C can be shared.


<a id="lauschkiste.hardware.Board"></a>

## Board Objects

```python
class Board(Protocol)
```

<a id="lauschkiste.hardware.Board.describe"></a>

#### describe

```python
def describe() -> Dict[str, Any]
```

``{'name', 'model', 'pins': [{'id', 'label', 'position', 'functions'}],

'interfaces': [{'id', 'label', 'pins'}]}``


<a id="lauschkiste.hardware.Board.pin_id"></a>

#### pin\_id

```python
def pin_id(value: Any) -> Optional[str]
```

The board's id of a pin given as the user wrote it (e.g. ``17`` or ``'GPIO17'``), None if unknown.


<a id="lauschkiste.hardware.Board.gpio_line"></a>

#### gpio\_line

```python
def gpio_line(pin: str) -> Tuple[int, int]
```

(gpiochip number, line) of a GPIO pin.


<a id="lauschkiste.hardware.Board.boot_pending"></a>

#### boot\_pending

```python
def boot_pending() -> List[str]
```

Settings that need the boot configuration changed (``lauschctl setup``) and a reboot.


<a id="lauschkiste.hardware.Hardware"></a>

## Hardware Objects

```python
class Hardware(CoreModule)
```

The board Lauschkiste runs on, its pins and who uses them; shutdown and reboot.


<a id="lauschkiste.hardware.Hardware.get_state"></a>

#### get\_state

```python
@query(path='/')
def get_state() -> HardwareState
```

The board, its pins and interfaces, who uses them, conflicts and pending boot changes.


<a id="lauschkiste.hardware.Hardware.pin_options"></a>

#### pin\_options

```python
@query(path='/pin-options')
def pin_options() -> List[Choice]
```

GPIO pins of the board for choosing in settings, with their current users.


<a id="lauschkiste.hardware.Hardware.gpio_line"></a>

#### gpio\_line

```python
@query(path='/gpio-line')
def gpio_line(pin: str) -> GpioLine
```

GPIO chip and line of a pin (for device plugins).


<a id="lauschkiste.hardware.Hardware.shutdown"></a>

#### shutdown

```python
@action()
def shutdown() -> None
```

Shut the box down.


<a id="lauschkiste.hardware.Hardware.reboot"></a>

#### reboot

```python
@action()
def reboot() -> None
```

Reboot the box.


<a id="lauschkiste.resume"></a>

# lauschkiste.resume

Continue items (audiobooks, podcast episodes) where they stopped.

An item is a list of files played in order through the player. While it plays, its position (file
and seconds) is taken from ``player.status`` and kept in a JSON file; it counts as finished once
its last file has played to the end.


<a id="lauschkiste.resume.relative"></a>

#### relative

```python
def relative(file: Optional[str]) -> Optional[str]
```

``file`` relative to the library if it is an absolute path below it.


<a id="lauschkiste.resume.PositionStore"></a>

## PositionStore Objects

```python
class PositionStore(Protocol)
```

Where the position of one item is kept when not in the tracker's own file (e.g. on a server).


<a id="lauschkiste.resume.ResumeTracker"></a>

## ResumeTracker Objects

```python
class ResumeTracker()
```

Positions of the items of one module, keyed by item id.


<a id="lauschkiste.resume.ResumeTracker.set_finished"></a>

#### set\_finished

```python
def set_finished(key: str, finished: bool) -> None
```

Mark an item as finished or forget it; either way it starts from the beginning next time.


<a id="lauschkiste.resume.ResumeTracker.play"></a>

#### play

```python
def play(key: str,
         files: List[str],
         resume: bool = True,
         context: Optional[Dict[str, Any]] = None,
         store: Optional[PositionStore] = None,
         names: Optional[List[str]] = None) -> None
```

Play an item: where it stopped (``resume``), else from the beginning. The item that is

already playing keeps playing, a paused one continues. With a ``store`` the position is read
from and reported to it instead of the tracker's file. ``names`` identify the files in the saved
position when they differ from what is played (a stream and its downloaded copy are the same file).


<a id="lauschkiste.player.coordinator"></a>

# lauschkiste.player.coordinator

<a id="lauschkiste.player.coordinator.PlayerCoordinator"></a>

## PlayerCoordinator Objects

```python
class PlayerCoordinator()
```

Provider-neutral facade for playback and content backends.


<a id="lauschkiste.player.coordinator.PlayerCoordinator.__init__"></a>

#### \_\_init\_\_

```python
def __init__(second_swipe_action: Optional[Callable[[], Any]] = None)
```

**Arguments**:

- `second_swipe_action`: runs on a second swipe of the same card instead of the
backend's own second-swipe behavior

<a id="lauschkiste.player.coordinator.PlayerCoordinator.register_backend"></a>

#### register\_backend

```python
def register_backend(name: str,
                     backend: Any,
                     make_active: bool = False) -> None
```

Register a backend, selecting the first registered backend by default.


<a id="lauschkiste.player.coordinator.PlayerCoordinator.set_default_backend"></a>

#### set\_default\_backend

```python
def set_default_backend(name: str) -> None
```

Make ``name`` the backend used for content without an explicit provider.


<a id="lauschkiste.player.coordinator.PlayerCoordinator.select_backend"></a>

#### select\_backend

```python
def select_backend(name: str)
```

Stop the current backend and select another registered backend.


<a id="lauschkiste.player.coordinator.PlayerCoordinator.set_speed"></a>

#### set\_speed

```python
def set_speed(speed)
```

Optional for backends; NotImplementedError if the active one can't change the speed.


<a id="lauschkiste.player.coordinator.PlayerCoordinator.play_files"></a>

#### play\_files

```python
def play_files(paths, start=0, position=0.0, ordered=False)
```

Play a list of songs (paths below the library, absolute or relative).


<a id="lauschkiste.player.module"></a>

# lauschkiste.player.module

The player core module: playback through registered backends, typed status events.


<a id="lauschkiste.player.module.Player"></a>

## Player Objects

```python
class Player(CoreModule)
```

Playback of folders, songs and albums; backends plug in at ``player.backends``.


<a id="lauschkiste.player.module.Player.play"></a>

#### play

```python
@action(path='/play')
def play() -> None
```

Start or resume playback.


<a id="lauschkiste.player.module.Player.pause"></a>

#### pause

```python
@action(path='/pause')
def pause(state: int = 1) -> None
```

Pause (state=1) or resume (state=0).


<a id="lauschkiste.player.module.Player.toggle"></a>

#### toggle

```python
@action(path='/toggle')
def toggle() -> None
```

Toggle between play and pause.


<a id="lauschkiste.player.module.Player.next"></a>

#### next

```python
@action(path='/next')
def next() -> None
```

Skip to the next song.


<a id="lauschkiste.player.module.Player.prev"></a>

#### prev

```python
@action(path='/prev')
def prev() -> None
```

Go back to the previous song.


<a id="lauschkiste.player.module.Player.stop_playback"></a>

#### stop\_playback

```python
@action(name='stop', path='/stop')
def stop_playback() -> None
```

Stop playback.


<a id="lauschkiste.player.module.Player.seek"></a>

#### seek

```python
@action(path='/seek')
def seek(position: float) -> None
```

Jump to a position (seconds) in the current song.


<a id="lauschkiste.player.module.Player.shuffle"></a>

#### shuffle

```python
@action(path='/shuffle')
def shuffle(option: str = 'toggle') -> None
```

Shuffle mode: 'toggle', 'enable' or 'disable'.


<a id="lauschkiste.player.module.Player.repeat"></a>

#### repeat

```python
@action(path='/repeat')
def repeat(option: str = 'toggle') -> None
```

Repeat mode: 'toggle', 'enable', 'enable_repeat_single' or 'disable'.


<a id="lauschkiste.player.module.Player.jump"></a>

#### jump

```python
@action(path='/jump')
def jump(position: int) -> None
```

Play the entry at ``position`` of the queue.


<a id="lauschkiste.player.module.Player.set_speed"></a>

#### set\_speed

```python
@action(path='/speed')
def set_speed(speed: float) -> None
```

Playback speed (0.5 to 2.0) of audiobooks and podcasts; music and radio always play at 1.0.


<a id="lauschkiste.player.module.Player.get_queue"></a>

#### get\_queue

```python
@query(path='/queue')
def get_queue() -> List[QueueEntry]
```

The queue with title and duration from the library.


<a id="lauschkiste.player.module.Player.stop_after_current"></a>

#### stop\_after\_current

```python
@action(path='/stop-after-current')
def stop_after_current(enabled: bool = True) -> None
```

Stop once the current song, chapter or episode has played to its end (sleep timer).


<a id="lauschkiste.player.module.Player.rewind"></a>

#### rewind

```python
@action(path='/rewind')
def rewind() -> None
```

Restart the playlist from its first song.


<a id="lauschkiste.player.module.Player.replay"></a>

#### replay

```python
@action(path='/replay')
def replay() -> None
```

Replay the current folder from the start.


<a id="lauschkiste.player.module.Player.replay_if_stopped"></a>

#### replay\_if\_stopped

```python
@action(path='/replay-if-stopped')
def replay_if_stopped() -> None
```

Replay the current folder if playback has stopped.


<a id="lauschkiste.player.module.Player.resume"></a>

#### resume

```python
@action(path='/resume')
def resume() -> None
```

Resume the last played folder where it stopped.


<a id="lauschkiste.player.module.Player.play_folder"></a>

#### play\_folder

```python
@action(path='/folder')
def play_folder(folder: str, recursive: bool = False) -> None
```

Play a folder of the music library.


<a id="lauschkiste.player.module.Player.play_card"></a>

#### play\_card

```python
@action()
def play_card(folder: str, recursive: bool = False) -> None
```

Play a folder; a second swipe of the same card runs the second-swipe action.


<a id="lauschkiste.player.module.Player.play_single"></a>

#### play\_single

```python
@action(path='/song')
def play_single(song_url: str, provider: Optional[str] = None) -> None
```

Play a single song.


<a id="lauschkiste.player.module.Player.play_album"></a>

#### play\_album

```python
@action(path='/album')
def play_album(albumartist: str,
               album: str,
               content_uri: Optional[str] = None,
               provider: Optional[str] = None) -> None
```

Play an album of the library or of a backend's own catalog (``provider``).


<a id="lauschkiste.player.module.Player.play_files"></a>

#### play\_files

```python
@action(path='/files')
def play_files(files: List[str],
               start: int = 0,
               position: float = 0.0,
               ordered: bool = False,
               context: Optional[PlaybackContext] = None) -> None
```

Play files of the library (or URLs), from ``position`` seconds into the file at index ``start``;

``ordered`` plays them in order, ignoring shuffle and repeat. ``context`` says what is played
(shown by the web app; without it, music).


<a id="lauschkiste.player.module.Player.queue_load"></a>

#### queue\_load

```python
@action(path='/queue')
def queue_load(folder: str) -> None
```

Load a folder into the queue without playing it.


<a id="lauschkiste.player.module.Player.update"></a>

#### update

```python
@action(path='/update')
def update() -> Any
```

Rescan the music library of the default backend.


<a id="lauschkiste.player.module.Player.update_wait"></a>

#### update\_wait

```python
@action(path='/update-wait')
def update_wait() -> Any
```

Rescan the music library and wait for it to finish.


<a id="lauschkiste.player.module.Player.playerstatus"></a>

#### playerstatus

```python
@query(path='/status')
def playerstatus() -> PlayerStatus
```

Current player status.


<a id="lauschkiste.player.module.Player.get_volume"></a>

#### get\_volume

```python
@query(path='/volume')
def get_volume() -> VolumeLevel
```

Current playback volume of the active backend.


<a id="lauschkiste.player.module.Player.set_volume"></a>

#### set\_volume

```python
@action(method='PUT', path='/volume')
def set_volume(volume: int) -> VolumeLevel
```

Set the playback volume of the active backend.


<a id="lauschkiste.player.module.Player.playlistinfo"></a>

#### playlistinfo

```python
@query(path='/playlist')
def playlistinfo() -> List[Dict[str, Any]]
```

The current queue.


<a id="lauschkiste.player.module.Player.get_current_song"></a>

#### get\_current\_song

```python
@query(path='/current-song')
def get_current_song(param: Optional[str] = None) -> Any
```

Details of the current song.


<a id="lauschkiste.player.module.Player.get_player_type_and_version"></a>

#### get\_player\_type\_and\_version

```python
@query(path='/type')
def get_player_type_and_version() -> str
```

Type and version of the active backend.


<a id="lauschkiste.player.module.Player.list_backends"></a>

#### list\_backends

```python
@query(path='/backends')
def list_backends() -> List[str]
```

Registered backends.


<a id="lauschkiste.player.module.Player.get_active_backend"></a>

#### get\_active\_backend

```python
@query(path='/backends/active')
def get_active_backend() -> BackendName
```

The backend playing right now.


<a id="lauschkiste.player.module.Player.get_default_backend"></a>

#### get\_default\_backend

```python
@query(path='/backends/default')
def get_default_backend() -> BackendName
```

The backend used for content without an explicit provider.


<a id="lauschkiste.player.module.Player.select_backend"></a>

#### select\_backend

```python
@action(method='PUT', path='/backends/active')
def select_backend(name: str) -> BackendName
```

Stop the current backend and switch to another one.


<a id="lauschkiste.player.status"></a>

# lauschkiste.player.status

Typed player status, independent of the backend that produced it.


<a id="lauschkiste.player.status.PlaybackContext"></a>

## PlaybackContext Objects

```python
class PlaybackContext(BaseModel)
```

What is playing: its content type, a title, and the card action that plays it.


<a id="lauschkiste.player.status.PlaybackContext.image"></a>

#### image

A picture of what plays (a station's logo, a podcast's artwork); shown when the file has no cover of its own


<a id="lauschkiste.player.status.PlayerStatus"></a>

## PlayerStatus Objects

```python
class PlayerStatus(BaseModel)
```

<a id="lauschkiste.player.status.PlayerStatus.name"></a>

#### name

Name of a stream (radio station)


<a id="lauschkiste.player.status.PlayerStatus.genre"></a>

#### genre

What the stream says about itself (radio): its genre and a short description


<a id="lauschkiste.player.status.status_from_backend"></a>

#### status\_from\_backend

```python
def status_from_backend(raw: Mapping[str, Any], provider: str) -> PlayerStatus
```

Build a :class:`PlayerStatus` from a backend's raw (mpd-style) status mapping.


<a id="lauschkiste.player"></a>

# lauschkiste.player

Playback: the player core module, its backends and the coordinator between them.


<a id="lauschkiste.player.backend"></a>

# lauschkiste.player.backend

Protocol a player backend implements to register at the ``player.backends`` extension point.

Optional capabilities (library browsing, cover art, rewind, ...) are looked up by name at call
time; a backend without them makes the corresponding operation answer 501.


<a id="lauschkiste.player.backend.PlayerBackend"></a>

## PlayerBackend Objects

```python
class PlayerBackend(Protocol)
```

<a id="lauschkiste.player.backend.PlayerBackend.set_status_callback"></a>

#### set\_status\_callback

```python
def set_status_callback(callback: Callable[[Mapping[str, Any]], None]) -> None
```

Receive the raw status mapping whenever it changes (only forwarded while active).


<a id="lauschkiste.player.backend.PlayerBackend.jump"></a>

#### jump

```python
def jump(position: int) -> None
```

Play the queue entry at ``position``.


<a id="lauschkiste.player.backend.PlayerBackend.stop_after_current"></a>

#### stop\_after\_current

```python
def stop_after_current(enabled: bool = True) -> None
```

Stop once the current entry has played to its end.


<a id="lauschkiste.player.backend.PlayerBackend.play_files"></a>

#### play\_files

```python
def play_files(paths: List[str],
               start: int = 0,
               position: float = 0.0,
               ordered: bool = False) -> None
```

Replace the queue with ``paths`` (absolute or relative to the library) and play from

``position`` seconds into the entry at index ``start``. ``ordered`` plays the queue in order,
ignoring shuffle and repeat until other content is played.


<a id="lauschkiste.player.backend.LevelMeter"></a>

## LevelMeter Objects

```python
class LevelMeter(Protocol)
```

<a id="lauschkiste.player.backend.LevelMeter.level"></a>

#### level

```python
def level(left: float, right: float, delay: float) -> None
```

RMS level (0..1) of each channel of the output, audible in ``delay`` seconds; about ten times a second

while playing (only with backends that can measure it, e.g. local_audio).


<a id="lauschkiste.player.backend.Resolver"></a>

## Resolver Objects

```python
class Resolver(Protocol)
```

<a id="lauschkiste.player.backend.Resolver.resolve"></a>

#### resolve

```python
def resolve(url: str) -> Tuple[str, Dict[str, str]]
```

The URL to open and the HTTP headers to send for a track URL with the scheme this resolver is

registered for (``player.resolvers``), so that credentials never appear in queues, status or logs.


<a id="lauschkiste.player.backends.local_audio"></a>

# lauschkiste.player.backends.local\_audio

Default player backend: decodes audio directly (PyAV) and writes PCM to the machine's normal

audio output (sounddevice/PortAudio) -- no mpd, no external player process, works on any Linux
box. See documentation/developers/roadmap-core-architecture.md, "Advanced plugin system".

Folder scanning reuses `lauschkiste.playlistgenerator.PlaylistCollector` (already backend-agnostic --
`backends/mpd.py` uses the exact same class, just pushes the resulting paths into MPD's queue
instead of this backend's own in-process one).

Playback runs on one dedicated worker thread. Every control method (play/pause/stop/next/prev/
seek/play_folder/...) updates `_state`/`_index`/`_position` under `_cv` and sets `_abort` to
interrupt whatever the worker is currently doing; the worker reopens/seeks the current track
whenever it's told to (re)start one. This keeps the state machine in one place instead of trying
to signal a live decode loop with finer-grained commands.


<a id="lauschkiste.player.backends.local_audio.ca_file"></a>

#### ca\_file

```python
def ca_file()
```

The CA bundle for https streams: the ffmpeg of the av wheels does not know the system's.


<a id="lauschkiste.player.backends.local_audio.PlayerLocalAudio"></a>

## PlayerLocalAudio Objects

```python
class PlayerLocalAudio()
```

Decode-and-output player backend. See module docstring for the state machine.


<a id="lauschkiste.player.backends.local_audio.PlayerLocalAudio.set_level_callback"></a>

#### set\_level\_callback

```python
def set_level_callback(callback)
```

``callback(left, right, delay)`` for the level of the output, or None.


<a id="lauschkiste.player.backends.local_audio.PlayerLocalAudio.rewind"></a>

#### rewind

```python
def rewind()
```

Re-start current playlist from the first track.


<a id="lauschkiste.player.backends.local_audio.PlayerLocalAudio.replay"></a>

#### replay

```python
def replay()
```

Re-start playing the last-played folder.


<a id="lauschkiste.player.backends"></a>

# lauschkiste.player.backends

Playback backend implementations used by the player coordinator.


