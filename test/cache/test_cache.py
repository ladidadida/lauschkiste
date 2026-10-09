import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from lauschkiste.cache import Cache, CacheFile, CachePlan
from lauschkiste.cache.manager import DownloadManager
from lauschkiste.cache.store import CacheStore
from lauschkiste.cache.worker import Download, DownloadError
from lauschkiste.cfghandler import ConfigHandler
from lauschkiste.contract import OperationError
from lauschkiste.contract.manager import ModuleManager
from lauschkiste.publishing.bus import EventBus

CONTENT = {'a.mp3': bytes(range(256)) * 4, 'b.mp3': b'B' * 3000, 'c.mp3': b'C' * 500}
TOKEN = 'Bearer secret'


class Handler(BaseHTTPRequestHandler):
    ranges = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.headers.get('Authorization') != TOKEN:
            self.send_response(401)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        content = CONTENT[self.path.lstrip('/')]
        header = self.headers.get('Range')
        type(self).ranges.append(header)
        start = int(header.split('=')[1].rstrip('-')) if header else 0
        body = content[start:]
        self.send_response(206 if header else 200)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def server():
    Handler.ranges = []
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{httpd.server_port}'
    httpd.shutdown()


def plan_for(server, names=('a.mp3', 'b.mp3', 'c.mp3'), token=TOKEN, version='v1'):
    return CachePlan(title='A book', version=version, files=[
        CacheFile(name=f'{number:03d}_{name}', url=f'{server}/{name}', size=len(CONTENT[name]), duration=10.0 * number,
                  headers={'Authorization': token}) for number, name in enumerate(names, 1)])


def prepare(store, plan, source='demo', item='one'):
    directory = store.directory(source, item)
    directory.mkdir(parents=True)
    (directory / 'plan.json').write_text(json.dumps(plan.model_dump(mode='json')))
    return directory


def test_the_worker_writes_all_files_and_marks_the_item_complete(server, tmp_path):
    store = CacheStore(tmp_path)
    directory = prepare(store, plan_for(server))
    Download(directory, store.rate_file, 'demo', 'one').run()
    meta = store.complete('demo', 'one')
    assert [f['name'] for f in meta['files']] == ['001_a.mp3', '002_b.mp3', '003_c.mp3']
    assert meta['title'] == 'A book' and meta['version'] == 'v1' and 'headers' not in json.dumps(meta)
    assert (directory / '001_a.mp3').read_bytes() == CONTENT['a.mp3']
    assert store.status_of('demo', 'one')['state'] == 'done'
    assert store.used_bytes() == sum(map(len, CONTENT.values()))


def test_a_partial_file_is_continued_with_a_range_request(server, tmp_path):
    store = CacheStore(tmp_path)
    directory = prepare(store, plan_for(server))
    (directory / '002_b.mp3.part').write_bytes(CONTENT['b.mp3'][:1000])
    Download(directory, store.rate_file).run()
    assert (directory / '002_b.mp3').read_bytes() == CONTENT['b.mp3']
    assert 'bytes=1000-' in Handler.ranges


def test_a_refused_access_is_an_error(server, tmp_path):
    store = CacheStore(tmp_path)
    directory = prepare(store, plan_for(server, token='Bearer wrong'))
    with pytest.raises(DownloadError, match='refused'):
        Download(directory, store.rate_file).run()


def test_a_wrong_size_is_an_error_and_leaves_nothing_half_done(server, tmp_path):
    store = CacheStore(tmp_path)
    plan = plan_for(server)
    plan.files[0].size += 5
    directory = prepare(store, plan)
    with pytest.raises(Exception):
        Download(directory, store.rate_file).run()
    assert not store.complete('demo', 'one')


def test_the_manager_runs_the_worker_process_and_removes_the_plan(server, tmp_path):
    store = CacheStore(tmp_path)
    manager = DownloadManager(store)
    directory = prepare(store, plan_for(server))
    manager.start('demo', 'one')
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline and not store.complete('demo', 'one'):
        time.sleep(0.1)
    assert store.complete('demo', 'one')
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and (directory / 'plan.json').exists():
        time.sleep(0.05)
    assert not (directory / 'plan.json').exists()
    assert [s['state'] for s in manager.states()] == ['done']
    manager.remove('demo', 'one')
    assert store.items() == []
    manager.close()


# -- the module ---------------------------------------------------------------------------------

class Provider:
    def __init__(self, server, version='v1', removable=False):
        self.server, self.current, self._removable = server, version, removable
        self.planned = []

    def plan(self, item):
        if item == 'nope':
            raise OperationError(404, 'unknown', 'no such item')
        self.planned.append(item)
        return plan_for(self.server, version=self.current)

    def version(self, item):
        return self.current

    def removable(self, item):
        return self._removable


@pytest.fixture
def cache(server, tmp_path, monkeypatch):
    import lauschkiste.paths
    monkeypatch.setenv(lauschkiste.paths.HOME_ENV, str(tmp_path))
    lauschkiste.paths.set_home(None)
    cfg = ConfigHandler('test')
    cfg.config_dict({'cache': {'limit_gb': 1}})
    manager = ModuleManager([Cache], cfg, EventBus(), plugins={}, strict=True)
    manager.load()
    manager.start()
    manager.ready()
    handle = manager.handle('cache')
    handle.provider = Provider(server)
    handle.instance.providers.register('demo', handle.provider)
    yield handle
    manager.stop()
    lauschkiste.paths.set_home(None)


def wait_done(handle, source='demo', item='one', timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found = [s for s in handle.invoke('downloads').items if s.item == item]
        if found and found[0].state in ('done', 'error'):
            return found[0]
        time.sleep(0.1)
    raise AssertionError('download did not finish')


def test_download_fetches_the_plan_writes_a_private_plan_file_and_completes(cache):
    cache.invoke('download', 'demo', 'one')
    state = wait_done(cache)
    assert state.state == 'done' and state.total == sum(map(len, CONTENT.values()))
    cached = cache.invoke('files', 'demo', 'one')
    assert cached.title == 'A book' and [f.duration for f in cached.files] == [10.0, 20.0, 30.0]
    assert open(cached.files[0].path, 'rb').read() == CONTENT['a.mp3']
    assert [c.item for c in cache.invoke('cached', 'demo')] == ['one']
    assert cache.invoke('files', 'demo', 'missing') is None
    assert not any(cache.instance._store.directory('demo', 'one').glob('plan.json'))


def test_a_complete_item_is_not_planned_again(cache):
    cache.invoke('download', 'demo', 'one')
    wait_done(cache)
    cache.invoke('download', 'demo', 'one')
    assert cache.provider.planned == ['one']


def test_unknown_source_item_and_invalid_names(cache):
    with pytest.raises(OperationError) as error:
        cache.invoke('download', 'other', 'one')
    assert error.value.status == 404
    with pytest.raises(OperationError) as error:
        cache.invoke('download', 'demo', '../x')
    assert error.value.status == 422
    with pytest.raises(OperationError) as error:
        cache.invoke('download', 'demo', 'nope')
    assert error.value.status == 404


def test_a_download_that_does_not_fit_is_refused_with_the_numbers(cache):
    cache.instance._ctx.config.set('limit_gb', value=0.0000001)
    with pytest.raises(OperationError) as error:
        cache.invoke('download', 'demo', 'one')
    assert error.value.status == 409 and 'MB' in error.value.message


def test_an_update_is_reported_when_the_provider_version_changes(cache):
    cache.invoke('download', 'demo', 'one')
    wait_done(cache)
    assert cache.invoke('downloads').items[0].update_available is False
    cache.provider.current = 'v2'
    assert cache.invoke('downloads').items[0].update_available is True


def test_old_removable_items_make_room_when_allowed(cache):
    cache.invoke('download', 'demo', 'one')
    wait_done(cache)
    cache.provider._removable = True
    total = sum(map(len, CONTENT.values()))
    config = cache.instance._ctx.config
    config.set('limit_gb', value=(total * 1.5) / (1 << 30))
    with pytest.raises(OperationError):
        cache.invoke('download', 'demo', 'two')
    config.set('remove_old', value=True)
    cache.invoke('download', 'demo', 'two')
    wait_done(cache, item='two')
    assert cache.invoke('files', 'demo', 'one') is None and cache.invoke('files', 'demo', 'two') is not None


def test_items_that_may_not_be_removed_stay_even_when_allowed(cache):
    cache.invoke('download', 'demo', 'one')
    wait_done(cache)
    total = sum(map(len, CONTENT.values()))
    config = cache.instance._ctx.config
    config.set('limit_gb', value=(total * 1.5) / (1 << 30))
    config.set('remove_old', value=True)
    with pytest.raises(OperationError):
        cache.invoke('download', 'demo', 'two')
    assert cache.invoke('files', 'demo', 'one') is not None


def test_remove_deletes_the_files(cache):
    cache.invoke('download', 'demo', 'one')
    wait_done(cache)
    cache.invoke('remove', 'demo', 'one')
    assert cache.invoke('files', 'demo', 'one') is None
    assert cache.invoke('downloads').used_bytes == 0


def test_the_speed_follows_the_playback(cache):
    cache.instance._on_status('player.status', {'state': 'play'})
    store = cache.instance._store
    assert store.rate_file.read_text() == '1000'
    cache.instance._ctx.config.set('rate_playing_kbps', value=0)
    cache.instance._playing = None
    cache.instance._on_status('player.status', {'state': 'play'})
    assert store.rate_file.read_text() == '-1'
    cache.instance._on_status('player.status', {'state': 'pause'})
    assert store.rate_file.read_text() == '0'
