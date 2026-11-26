import json
import time
from fractions import Fraction
from unittest.mock import Mock

import av
import pytest

import lauschkiste.content.library
import lauschkiste.content.resume
from lauschkiste.content.audiobooks import Audiobooks
from lauschkiste.content.cache.module import Cache
from lauschkiste.common.cfghandler import ConfigHandler
from lauschkiste.contract import OperationError
from lauschkiste.contract.manager import ModuleManager
from lauschkiste.content.library.module import Library
from lauschkiste.player.module import Player
from lauschkiste.common.publishing.bus import EventBus


def write_flac(path, **tags):
    from mutagen.flac import FLAC
    path.parent.mkdir(parents=True, exist_ok=True)
    with av.open(str(path), 'w', format='flac') as container:
        stream = container.add_stream('flac', rate=8000)
        stream.layout = 'mono'
        frame = av.AudioFrame(format='s16', layout='mono', samples=800)
        frame.planes[0].update(bytes(frame.planes[0].buffer_size))
        frame.rate = 8000
        frame.time_base = Fraction(1, 8000)
        frame.pts = 0
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)
    audio = FLAC(str(path))
    for key, value in tags.items():
        audio[key] = value
    audio.save()


def wait_for(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


BOOK = ['audiobooks/Pippi/2.flac', 'audiobooks/Pippi/10.flac', 'audiobooks/Pippi/11.flac']


@pytest.fixture
def library_dir(tmp_path):
    root = tmp_path / 'library'
    for file in BOOK:
        write_flac(root / file, album='Pippi Langstrumpf')
    write_flac(root / 'audiobooks' / 'Emil' / '01.flac')
    write_flac(root / 'music' / 'Rock' / '01.flac', album='Loud')
    return root


@pytest.fixture
def setup(tmp_path, library_dir, monkeypatch):
    monkeypatch.setattr(lauschkiste.content.resume, 'ACTIVATION_GRACE_SEC', 0)
    monkeypatch.setattr(lauschkiste.content.library, 'root', lambda: str(library_dir))
    ctrl = Mock()
    ctrl.get_active_backend.return_value = 'local_audio'
    ctrl.playerstatus.return_value = {'state': 'play', 'file': 'music/Rock/01.flac', 'random': '1', 'repeat': '0'}

    class TestPlayer(Player):
        def start(self, ctx):
            self._ctx = ctx
            self._coordinator = ctrl

        def ready(self):
            pass

        def stop(self):
            return []

    state_file = tmp_path / 'audiobooks.json'
    cfg = ConfigHandler('test')
    cfg.config_dict({'library': {'path': str(library_dir), 'index': str(tmp_path / 'index.sqlite'),
                                 'cover_cache': str(tmp_path / 'covers'), 'watch': False},
                     'audiobooks': {'state_file': str(state_file), 'save_interval_sec': 0}})
    bus = EventBus()
    events = []
    bus.register(lambda topic, payload: events.append(topic))
    managers = []

    def start():
        manager = ModuleManager([Library, TestPlayer, Audiobooks, Cache], cfg, bus, plugins={}, strict=True)
        manager.load()
        manager.start()
        manager.ready()
        managers.append(manager)
        assert wait_for(lambda: 'library.scanned' in events)
        events.clear()
        return manager.handle('audiobooks')

    start.managers = managers

    def status(**values):
        bus.publish('player.status', {'provider': 'local_audio', 'state': 'play', **values})

    yield start, ctrl, status, state_file
    for manager in managers:
        manager.stop()


def test_lists_audiobooks_with_chapters_in_file_name_order(setup):
    start, _, _, _ = setup
    books = start().invoke('list_books')
    assert [(b.book, b.title, b.chapters, b.chapter, b.listened, b.finished) for b in books] == [
        ('Emil', 'Emil', 1, 0, 0.0, False),
        ('Pippi', 'Pippi Langstrumpf', 3, 0, 0.0, False),
    ]
    assert books[1].duration == pytest.approx(0.3, abs=0.03)


def test_play_continues_where_it_stopped(setup):
    start, ctrl, status, state_file = setup
    audiobooks = start()

    audiobooks.invoke('play', 'Pippi')
    ctrl.play_files.assert_called_once_with(BOOK, 0, 0.0, True)
    ctrl.playerstatus.return_value = {'state': 'play', 'file': BOOK[0], 'song': '0'}
    context = start.managers[-1].handle('player').invoke('playerstatus').context
    assert (context.kind, context.title, context.action, context.args) == (
        'audiobook', 'Pippi Langstrumpf', 'audiobooks.play', {'book': 'Pippi'})

    status(file=BOOK[1], elapsed='70.0', duration='300')
    status(file=BOOK[1], state='pause', elapsed='75.5', duration='300')
    assert wait_for(lambda: state_file.exists() and json.loads(state_file.read_text())['Pippi']['elapsed'] == 75.5)

    status(file='music/Rock/01.flac')
    book = [b for b in audiobooks.invoke('list_books') if b.book == 'Pippi'][0]
    assert (book.chapter, book.elapsed) == (1, 75.5)

    ctrl.play_files.reset_mock()
    audiobooks.invoke('play', 'Pippi')
    ctrl.play_files.assert_called_once_with(BOOK, 1, 65.5, True)


def test_position_survives_a_restart(setup):
    start, ctrl, status, state_file = setup
    audiobooks = start()
    audiobooks.invoke('play', 'Pippi')
    status(file=BOOK[2], elapsed='20', duration='300')
    assert wait_for(lambda: state_file.exists())

    ctrl.play_files.reset_mock()
    ctrl.playerstatus.return_value = {'state': 'stop'}
    start().invoke('play', 'Pippi')
    ctrl.play_files.assert_called_once_with(BOOK, 2, 10.0, True)


def test_playing_the_active_book_again_keeps_playing_or_resumes(setup):
    start, ctrl, _, _ = setup
    audiobooks = start()
    audiobooks.invoke('play', 'Pippi')
    ctrl.play_files.reset_mock()

    ctrl.playerstatus.return_value = {'state': 'play', 'file': BOOK[0]}
    audiobooks.invoke('play', 'Pippi')
    ctrl.playerstatus.return_value = {'state': 'pause', 'file': BOOK[0]}
    audiobooks.invoke('play', 'Pippi')
    ctrl.play_files.assert_not_called()
    ctrl.play.assert_called_once()

    audiobooks.invoke('restart', 'Pippi')
    ctrl.play_files.assert_called_once_with(BOOK, 0, 0.0, True)


def test_reaching_the_end_marks_the_book_finished(setup):
    start, ctrl, status, _ = setup
    audiobooks = start()
    audiobooks.invoke('play', 'Pippi')
    status(file=BOOK[2], elapsed='295', duration='300')
    status(file=BOOK[2], state='stop', elapsed='0', duration='300')
    book = [b for b in audiobooks.invoke('list_books') if b.book == 'Pippi'][0]
    assert book.finished and book.listened == book.duration

    ctrl.play_files.reset_mock()
    audiobooks.invoke('play', 'Pippi')
    ctrl.play_files.assert_called_once_with(BOOK, 0, 0.0, True)
    ctrl.playerstatus.return_value = {'state': 'play', 'file': BOOK[0], 'song': '0'}
    context = start.managers[-1].handle('player').invoke('playerstatus').context
    assert (context.kind, context.title, context.action, context.args) == (
        'audiobook', 'Pippi Langstrumpf', 'audiobooks.play', {'book': 'Pippi'})


def test_a_finished_book_played_again_from_the_box_is_followed(setup):
    start, _, status, state_file = setup
    audiobooks = start()
    audiobooks.invoke('play', 'Pippi')
    status(file=BOOK[2], elapsed='295', duration='300')
    status(file=BOOK[0], state='stop', elapsed='0', duration='300')
    assert [b.finished for b in audiobooks.invoke('list_books') if b.book == 'Pippi'] == [True]

    status(file=BOOK[0], state='stop', elapsed='0', duration='300')
    assert [b.finished for b in audiobooks.invoke('list_books') if b.book == 'Pippi'] == [True]

    status(file=BOOK[0], elapsed='30', duration='300')
    book = [b for b in audiobooks.invoke('list_books') if b.book == 'Pippi'][0]
    assert (book.finished, book.chapter, book.elapsed) == (False, 0, 30.0)


def test_stopping_after_a_chapter_continues_with_the_next(setup):
    start, ctrl, status, _ = setup
    audiobooks = start()
    audiobooks.invoke('play', 'Pippi')
    status(file=BOOK[0], elapsed='298', duration='300')
    status(file=BOOK[1], state='stop', elapsed='0', duration='300')
    book = [b for b in audiobooks.invoke('list_books') if b.book == 'Pippi'][0]
    assert (book.finished, book.chapter, book.elapsed) == (False, 1, 0.0)


def test_a_book_loaded_paused_keeps_its_saved_position(setup):
    start, ctrl, status, state_file = setup
    audiobooks = start()
    audiobooks.invoke('play', 'Pippi')
    status(file=BOOK[1], state='pause', elapsed='75', duration='300')
    assert wait_for(lambda: state_file.exists() and json.loads(state_file.read_text())['Pippi']['elapsed'] == 75)

    start.managers.pop().stop()
    ctrl.playerstatus.return_value = {'state': 'stop'}
    audiobooks = start()
    audiobooks.invoke('play', 'Pippi')
    ctrl.play_files.assert_called_with(BOOK, 1, 65.0, True)
    status(file=BOOK[1], state='pause', elapsed='65.000', duration='300')
    book = [b for b in audiobooks.invoke('list_books') if b.book == 'Pippi'][0]
    assert (book.chapter, book.elapsed) == (1, 75.0)

    status(file=BOOK[1], elapsed='66', duration='300')
    book = [b for b in audiobooks.invoke('list_books') if b.book == 'Pippi'][0]
    assert (book.chapter, book.elapsed) == (1, 66.0)


def test_stopping_in_the_middle_keeps_the_position(setup):
    start, _, status, _ = setup
    audiobooks = start()
    audiobooks.invoke('play', 'Pippi')
    status(file=BOOK[0], elapsed='12', duration='300')
    status(file=BOOK[0], state='stop', elapsed='0', duration='300')
    book = [b for b in audiobooks.invoke('list_books') if b.book == 'Pippi'][0]
    assert (book.finished, book.chapter, book.elapsed) == (False, 0, 12.0)


def test_set_finished_and_back(setup):
    start, _, _, _ = setup
    audiobooks = start()
    audiobooks.invoke('set_finished', 'Emil')
    assert [b.finished for b in audiobooks.invoke('list_books') if b.book == 'Emil'] == [True]
    audiobooks.invoke('set_finished', 'Emil', False)
    assert [b.finished for b in audiobooks.invoke('list_books') if b.book == 'Emil'] == [False]


@pytest.mark.parametrize('book, status', [('Nope', 404), ('../music', 422), ('', 422)])
def test_unknown_or_invalid_books(setup, book, status):
    start, _, _, _ = setup
    with pytest.raises(OperationError) as error:
        start().invoke('play', book)
    assert error.value.status == status


def test_a_title_set_in_the_web_app_replaces_the_tag_until_it_is_cleared(setup, library_dir):
    start, ctrl, _, _ = setup
    audiobooks = start()
    audiobooks.invoke('set_title', 'Pippi', '  Pippi in Taka-Tuka-Land ')
    assert json.loads((library_dir / 'audiobooks' / 'Pippi' / 'book.json').read_text()) == {
        'title': 'Pippi in Taka-Tuka-Land'}
    pippi = next(b for b in audiobooks.invoke('list_books') if b.book == 'Pippi')
    assert (pippi.title, pippi.custom_title) == ('Pippi in Taka-Tuka-Land', True)
    audiobooks.invoke('play', 'Pippi')
    ctrl.playerstatus.return_value = {'state': 'play', 'file': BOOK[0], 'song': '0'}
    assert start.managers[-1].handle('player').invoke('playerstatus').context.title == 'Pippi in Taka-Tuka-Land'

    audiobooks.invoke('set_title', 'Pippi', '')
    assert not (library_dir / 'audiobooks' / 'Pippi' / 'book.json').exists()
    pippi = next(b for b in audiobooks.invoke('list_books') if b.book == 'Pippi')
    assert (pippi.title, pippi.custom_title) == ('Pippi Langstrumpf', False)


def test_clearing_the_title_keeps_other_entries_of_book_json(setup, library_dir):
    start, _, _, _ = setup
    book_file = library_dir / 'audiobooks' / 'Emil' / 'book.json'
    book_file.write_text(json.dumps({'title': 'Emil und die Detektive', 'author': 'Kästner'}))
    audiobooks = start()
    assert [b.title for b in audiobooks.invoke('list_books') if b.book == 'Emil'] == ['Emil und die Detektive']
    audiobooks.invoke('set_title', 'Emil', '')
    assert json.loads(book_file.read_text()) == {'author': 'Kästner'}


def test_a_broken_book_json_is_ignored(setup, library_dir):
    start, _, _, _ = setup
    (library_dir / 'audiobooks' / 'Emil' / 'book.json').write_text('{nope')
    assert [b.title for b in start().invoke('list_books') if b.book == 'Emil'] == ['Emil']


@pytest.mark.parametrize('book, status', [('Nope', 404), ('../music', 422)])
def test_set_title_of_unknown_or_invalid_books(setup, book, status):
    start, _, _, _ = setup
    with pytest.raises(OperationError) as error:
        start().invoke('set_title', book, 'X')
    assert error.value.status == status


PNG = bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'
                    '1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082')


def test_chapters_can_be_reordered_and_renamed(setup, library_dir):
    start, ctrl, _, _ = setup
    audiobooks = start()
    details = audiobooks.invoke('edit_book', 'Pippi', 'Pippi', 'Astrid Lindgren', [
        {'file': '11.flac', 'title': 'Das Ende'}, {'file': '2.flac', 'title': ''}])
    assert [(c.file, c.title) for c in details.chapters] == [('11.flac', 'Das Ende'), ('2.flac', '2'), ('10.flac', '10')]
    assert (details.title, details.author) == ('Pippi', 'Astrid Lindgren')
    pippi = next(b for b in audiobooks.invoke('list_books') if b.book == 'Pippi')
    assert (pippi.title, pippi.author, pippi.custom_title) == ('Pippi', 'Astrid Lindgren', True)

    audiobooks.invoke('play', 'Pippi')
    ctrl.play_files.assert_called_once_with([BOOK[2], BOOK[0], BOOK[1]], 0, 0.0, True)
    ctrl.playerstatus.return_value = {'state': 'play', 'file': str(library_dir / BOOK[2]), 'song': '0'}
    assert start.managers[-1].handle('player').invoke('playerstatus').title == 'Das Ende'

    audiobooks.invoke('edit_book', 'Pippi', '', '', [])
    assert not (library_dir / 'audiobooks' / 'Pippi' / 'book.json').exists()
    details = audiobooks.invoke('get_book', 'Pippi')
    assert [c.file for c in details.chapters] == ['2.flac', '10.flac', '11.flac']
    assert (details.title, details.author) == ('Pippi Langstrumpf', None)


def test_editing_without_chapters_keeps_their_order(setup, library_dir):
    start, _, _, _ = setup
    audiobooks = start()
    audiobooks.invoke('edit_book', 'Pippi', chapters=[{'file': '10.flac'}])
    audiobooks.invoke('edit_book', 'Pippi', author='Lindgren')
    assert [c.file for c in audiobooks.invoke('get_book', 'Pippi').chapters] == ['10.flac', '2.flac', '11.flac']


@pytest.mark.parametrize('chapters', [[{'file': 'nope.flac'}], [{'file': '2.flac'}, {'file': '2.flac'}]])
def test_unknown_or_repeated_chapters_are_refused(setup, chapters):
    start, _, _, _ = setup
    with pytest.raises(OperationError) as error:
        start().invoke('edit_book', 'Pippi', chapters=chapters)
    assert error.value.status == 422


def test_a_cover_can_be_uploaded_and_removed(setup, library_dir):
    start, _, _, _ = setup
    audiobooks = start()
    module = start.managers[-1].handle('audiobooks').instance
    saved = module._save_cover('Emil', 'Titel.PNG', PNG)
    assert saved.cover_url and saved.cover_url.endswith('.png')
    assert (library_dir / 'audiobooks' / 'Emil' / 'book-cover.png').read_bytes() == PNG
    emil = next(b for b in audiobooks.invoke('list_books') if b.book == 'Emil')
    assert emil.cover_url == saved.cover_url
    assert audiobooks.invoke('get_book', 'Emil').custom_cover

    audiobooks.invoke('play', 'Emil')
    status = start.managers[-1].handle('player').invoke('playerstatus')
    assert status.cover_url == saved.cover_url

    audiobooks.invoke('remove_cover', 'Emil')
    assert not (library_dir / 'audiobooks' / 'Emil' / 'book-cover.png').exists()
    assert not (library_dir / 'audiobooks' / 'Emil' / 'book.json').exists()
    assert not audiobooks.invoke('get_book', 'Emil').custom_cover


def test_only_images_are_taken_as_cover(setup):
    start, _, _, _ = setup
    start()
    module = start.managers[-1].handle('audiobooks').instance
    with pytest.raises(OperationError) as error:
        module._save_cover('Emil', 'cover.txt', b'x')
    assert error.value.status == 415


class FakeSource:
    def __init__(self):
        self.saved = []
        self.stored = {'file': 'fake://b/2', 'elapsed': 40.0, 'finished': False}
        self.finished = []

    def list_books(self):
        return [{'book': 'b', 'title': 'Remote', 'chapters': 2, 'duration': 200.0, 'listened': 40.0}]

    def files(self, book):
        return ['fake://b/1', 'fake://b/2']

    def title(self, book):
        return 'Remote book'

    def position(self, book):
        source = self

        class Store:
            def load(self):
                return dict(source.stored)

            def save(self, entry):
                source.saved.append(entry)

        return Store()

    def set_finished(self, book, finished):
        self.finished.append((book, finished))


def test_books_of_a_source_are_listed_and_play_from_the_source_position(setup):
    start, ctrl, status, state_file = setup
    audiobooks = start()
    source = FakeSource()
    start.managers[-1].handle('audiobooks').instance.sources.register('fake', source)

    books = audiobooks.invoke('list_books')
    assert [(b.source, b.book, b.title) for b in books] == [
        ('local', 'Emil', 'Emil'), ('local', 'Pippi', 'Pippi Langstrumpf'), ('fake', 'b', 'Remote')]

    audiobooks.invoke('play', 'b', 'fake')
    ctrl.play_files.assert_called_once_with(['fake://b/1', 'fake://b/2'], 1, 30.0, True)
    context = start.managers[-1].handle('player').invoke('playerstatus').context
    assert (context.title, context.args) == ('Remote book', {'book': 'b', 'source': 'fake'})

    status(file='fake://b/2', elapsed='50.0', duration='100')
    status(file='fake://b/2', state='pause', elapsed='55.0', duration='100')
    assert wait_for(lambda: source.saved and source.saved[-1]['elapsed'] == 55.0)
    assert not state_file.exists() or 'b' not in json.loads(state_file.read_text())


def test_finishing_the_last_file_of_a_source_book_is_reported(setup):
    start, ctrl, status, _ = setup
    audiobooks = start()
    source = FakeSource()
    start.managers[-1].handle('audiobooks').instance.sources.register('fake', source)
    audiobooks.invoke('play', 'b', 'fake')
    status(file='fake://b/2', elapsed='95.0', duration='100')
    status(file='fake://b/2', state='stop', elapsed='0', duration='100')
    assert wait_for(lambda: {'finished': True} in source.saved)


def test_a_failing_source_leaves_the_others(setup):
    start, _, _, _ = setup
    audiobooks = start()

    class Broken(FakeSource):
        def list_books(self):
            raise RuntimeError('down')

    start.managers[-1].handle('audiobooks').instance.sources.register('broken', Broken())
    assert [b.source for b in audiobooks.invoke('list_books')] == ['local', 'local']


def test_unknown_source_and_set_finished_on_a_source(setup):
    start, _, _, _ = setup
    audiobooks = start()
    with pytest.raises(OperationError) as error:
        audiobooks.invoke('play', 'b', 'nowhere')
    assert error.value.status == 404
    source = FakeSource()
    start.managers[-1].handle('audiobooks').instance.sources.register('fake', source)
    audiobooks.invoke('set_finished', 'b', True, 'fake')
    assert source.finished == [('b', True)]


def test_a_track_that_cannot_be_opened_does_not_overwrite_the_source_position(setup):
    start, _, status, _ = setup
    audiobooks = start()
    source = FakeSource()
    start.managers[-1].handle('audiobooks').instance.sources.register('fake', source)
    audiobooks.invoke('play', 'b', 'fake')
    status(file='fake://b/2', state='stop', elapsed='0')
    status(file='fake://b/2', state='play', elapsed='0')
    time.sleep(0.3)
    assert source.saved == []


def test_an_unchanged_position_is_not_reported_again(setup):
    start, _, status, _ = setup
    audiobooks = start()
    source = FakeSource()
    start.managers[-1].handle('audiobooks').instance.sources.register('fake', source)
    audiobooks.invoke('play', 'b', 'fake')
    status(file='fake://b/2', state='pause', elapsed='55.0', duration='100')
    assert wait_for(lambda: len(source.saved) == 1)
    for _ in range(5):
        status(file='fake://b/2', state='pause', elapsed='55.0', duration='100')
    time.sleep(0.3)
    assert len(source.saved) == 1
    status(file='fake://b/2', state='pause', elapsed='56.0', duration='100')
    assert wait_for(lambda: len(source.saved) == 2)


class CacheProvider:
    def plan(self, item):
        raise NotImplementedError

    def version(self, item):
        return None

    def removable(self, item):
        return False


def test_books_say_where_they_come_from(setup):
    start, _, _, _ = setup
    audiobooks = start()
    manager = start.managers[-1]
    manager.handle('audiobooks').instance.sources.register('fake', FakeSource())
    manager.handle('cache').instance.providers.register('fake', CacheProvider())
    assert {(b.source, b.availability) for b in audiobooks.invoke('list_books')} == {
        ('local', 'local'), ('fake', 'stream')}

    store = manager.handle('cache').instance._store
    directory = store.directory('fake', 'b')
    directory.mkdir(parents=True)
    (directory / 'f.mp3').write_bytes(b'12345')
    (directory / 'meta.json').write_text('{"title": "Remote", "files": [{"name": "f.mp3", "size": 5, "duration": 1}]}')
    assert {(b.source, b.availability) for b in audiobooks.invoke('list_books')} == {
        ('local', 'local'), ('fake', 'cached')}


def test_an_audiobook_can_be_taken_off_the_continue_list_until_it_is_played_on(setup):
    start, ctrl, status, _ = setup
    audiobooks = start()
    audiobooks.invoke('play', 'Pippi')
    status(file=BOOK[1], elapsed='70.0', duration='300')
    status(file=BOOK[1], state='pause', elapsed='75.5', duration='300')
    assert wait_for(lambda: [b for b in audiobooks.invoke('list_books') if b.book == 'Pippi'][0].listened > 0)
    pippi = lambda: [b for b in audiobooks.invoke('list_books') if b.book == 'Pippi'][0]  # noqa: E731
    assert pippi().hidden is False
    audiobooks.invoke('hide_from_continue', 'Pippi')
    assert pippi().hidden is True
    status(file=BOOK[1], state='pause', elapsed='120.0', duration='300')
    assert wait_for(lambda: pippi().hidden is False)
    with pytest.raises(OperationError):
        audiobooks.invoke('hide_from_continue', 'Nope')
