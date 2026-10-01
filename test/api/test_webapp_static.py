import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from starlette.testclient import TestClient

from lauschkiste.api.events import EventBroker
from lauschkiste.api.fastapi_server import create_app


def _make_client(build_dir=None, logs_dir=None):
    executor = ThreadPoolExecutor(max_workers=1)
    app = create_app(
        EventBroker(),
        executor,
        webapp_build_dir=build_dir,
        logs_dir=logs_dir,
    )
    return TestClient(app), executor


def test_missing_build_serves_fallback_page():
    with tempfile.TemporaryDirectory() as tmp:
        client, executor = _make_client(build_dir=Path(tmp) / 'does-not-exist')
        try:
            response = client.get('/')
            assert response.status_code == 200
            assert 'bundle is missing' in response.text
        finally:
            executor.shutdown(wait=True, cancel_futures=True)


def test_serves_index_html_with_no_store_and_static_assets():
    with tempfile.TemporaryDirectory() as tmp:
        build_dir = Path(tmp)
        (build_dir / 'index.html').write_text('<html>the webapp</html>')
        (build_dir / 'static').mkdir()
        (build_dir / 'static' / 'app.js').write_text('console.log(1)')

        client, executor = _make_client(build_dir=build_dir)
        try:
            index_response = client.get('/')
            assert index_response.status_code == 200
            assert index_response.text == '<html>the webapp</html>'
            assert index_response.headers['cache-control'] == 'no-store'

            index_html_response = client.get('/index.html')
            assert index_html_response.status_code == 200
            assert index_html_response.text == '<html>the webapp</html>'

            static_response = client.get('/static/app.js')
            assert static_response.status_code == 200
            assert static_response.text == 'console.log(1)'
        finally:
            executor.shutdown(wait=True, cancel_futures=True)


def test_unknown_path_gets_generic_404_not_index_html():
    with tempfile.TemporaryDirectory() as tmp:
        build_dir = Path(tmp)
        (build_dir / 'index.html').write_text('<html>the webapp</html>')

        client, executor = _make_client(build_dir=build_dir)
        try:
            response = client.get('/some/deep-link/route')
            assert response.status_code == 404
            assert 'Not found' in response.text
        finally:
            executor.shutdown(wait=True, cancel_futures=True)


def test_root_level_build_file_is_served_by_catch_all():
    with tempfile.TemporaryDirectory() as tmp:
        build_dir = Path(tmp)
        (build_dir / 'index.html').write_text('<html>the webapp</html>')
        (build_dir / 'favicon.ico').write_bytes(b'\x00')

        client, executor = _make_client(build_dir=build_dir)
        try:
            response = client.get('/favicon.ico')
            assert response.status_code == 200
        finally:
            executor.shutdown(wait=True, cancel_futures=True)


def test_hashed_assets_are_cached_everything_else_is_not():
    with tempfile.TemporaryDirectory() as tmp:
        build_dir = Path(tmp)
        (build_dir / 'index.html').write_text('<html>the webapp</html>')
        (build_dir / 'assets').mkdir()
        (build_dir / 'assets' / 'index-Ab12Cd.js').write_text('console.log(1)')
        (build_dir / 'locales' / 'de').mkdir(parents=True)
        (build_dir / 'locales' / 'de' / 'translation.json').write_text('{}')

        client, executor = _make_client(build_dir=build_dir)
        try:
            asset = client.get('/assets/index-Ab12Cd.js')
            assert asset.headers['cache-control'] == 'public, max-age=31536000, immutable'
            translation = client.get('/locales/de/translation.json')
            assert translation.status_code == 200
            assert translation.headers['cache-control'] == 'no-store'
        finally:
            executor.shutdown(wait=True, cancel_futures=True)


def test_catch_all_rejects_path_traversal_outside_build_dir():
    with tempfile.TemporaryDirectory() as tmp:
        build_dir = Path(tmp) / 'build'
        build_dir.mkdir()
        (build_dir / 'index.html').write_text('<html>the webapp</html>')
        secret = Path(tmp) / 'secret.txt'
        secret.write_text('do not serve me')

        client, executor = _make_client(build_dir=build_dir)
        try:
            response = client.get('/../secret.txt')
            assert response.status_code == 404
            assert 'do not serve me' not in response.text
        finally:
            executor.shutdown(wait=True, cancel_futures=True)


def test_logs_listing_and_file_serving():
    with tempfile.TemporaryDirectory() as tmp:
        logs_dir = Path(tmp)
        (logs_dir / 'app.log').write_text('hello log')

        client, executor = _make_client(logs_dir=logs_dir)
        try:
            listing = client.get('/logs')
            assert listing.status_code == 200
            assert 'app.log' in listing.text

            log_file = client.get('/logs/app.log')
            assert log_file.status_code == 200
            assert log_file.text == 'hello log'
        finally:
            executor.shutdown(wait=True, cancel_futures=True)


def test_logs_rejects_path_traversal():
    with tempfile.TemporaryDirectory() as tmp:
        logs_dir = Path(tmp) / 'logs'
        logs_dir.mkdir()
        secret = Path(tmp) / 'secret.txt'
        secret.write_text('do not serve me')

        client, executor = _make_client(logs_dir=logs_dir)
        try:
            response = client.get('/logs/..%2Fsecret.txt')
            assert response.status_code == 404
        finally:
            executor.shutdown(wait=True, cancel_futures=True)
