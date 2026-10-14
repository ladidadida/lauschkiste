import pytest

from lauschkiste.box.kiosk.module import Kiosk
from lauschkiste.box.kiosk.standard import KioskStandard
from lauschkiste.contract import CoreModule


class OwnApp(CoreModule):
    """A kiosk app of another module."""

    name = 'own_kiosk'
    requires = ('kiosk',)
    title = 'Own'
    entry = 'start.html'
    folder = None

    def start(self, ctx):
        ctx.modules.kiosk.apps.register(self.name, self)

    def directory(self):
        return self.folder


@pytest.fixture
def kiosk(api_client, tmp_path, monkeypatch):
    build = tmp_path / 'build'
    (build / 'assets').mkdir(parents=True)
    (build / 'kiosk.html').write_text('<html>standard</html>')
    (build / 'assets' / 'app-1.js').write_text('1')
    (build / 'secret.txt').write_text('x')
    monkeypatch.setattr('lauschkiste.api.fastapi_server.default_webapp_build_dir', lambda: build)
    monkeypatch.setattr('lauschkiste.common.paths.home', lambda: tmp_path)
    contexts = []

    def make(config=None, modules=()):
        context = api_client([Kiosk, KioskStandard, *modules], config)
        contexts.append(context)
        return context.__enter__()

    yield make, build, tmp_path
    for context in contexts:
        context.__exit__(None, None, None)


def test_off_by_default_the_screen_gets_the_normal_web_app(kiosk):
    make, _, _ = kiosk
    client = make()
    response = client.get('/kiosk/', follow_redirects=False)
    assert response.status_code == 307 and response.headers['location'] == '/?kiosk'
    assert client.get('/api/v1/kiosk/state').json() == {
        'enabled': False, 'app': 'kiosk_standard', 'apps': [{'value': 'kiosk_standard', 'label': 'Standard'}]}


def test_on_serves_the_entry_of_the_app_and_its_files(kiosk):
    make, _, _ = kiosk
    client = make({'kiosk': {'enabled': True}})
    page = client.get('/kiosk/')
    assert page.text == '<html>standard</html>' and page.headers['cache-control'] == 'no-store'
    assert client.get('/kiosk', follow_redirects=False).headers['location'] == '/kiosk/'
    asset = client.get('/kiosk/assets/app-1.js')
    assert asset.text == '1' and 'immutable' in asset.headers['cache-control']


def test_files_outside_the_app_folder_are_not_served(kiosk):
    make, build, tmp_path = kiosk
    (tmp_path / 'outside.txt').write_text('no')
    client = make({'kiosk': {'enabled': True}})
    assert client.get('/kiosk/missing.js').status_code == 404
    assert client.get('/kiosk/%2e%2e/outside.txt').status_code == 404


def test_another_app_can_be_chosen_and_the_built_in_one_takes_over_when_it_is_gone(kiosk):
    make, build, tmp_path = kiosk
    folder = tmp_path / 'own'
    folder.mkdir()
    (folder / 'start.html').write_text('<html>own</html>')
    OwnApp.folder = folder
    client = make({'kiosk': {'enabled': True, 'app': 'own_kiosk'}}, [OwnApp])
    assert client.get('/kiosk/').text == '<html>own</html>'
    assert [a['label'] for a in client.get('/api/v1/kiosk/apps').json()] == ['Standard', 'Own']

    gone = make({'kiosk': {'enabled': True, 'app': 'removed'}})
    assert gone.get('/kiosk/').text == '<html>standard</html>'


def test_settings_changes_are_published_as_state(kiosk):
    make, _, _ = kiosk
    client = make()
    response = client.put('/api/v1/settings/modules/kiosk', json={'values': {'enabled': True}})
    assert response.status_code == 200
    assert client.get('/kiosk/').text == '<html>standard</html>'


def test_standard_app_lists_built_in_and_own_themes(kiosk):
    make, _, tmp_path = kiosk
    (tmp_path / 'kiosk-themes').mkdir()
    (tmp_path / 'kiosk-themes' / 'my-theme.css').write_text(':root { --kiosk-mode: dark; }')
    (tmp_path / 'kiosk-themes' / 'night.css').write_text(':root { --kiosk-mode: light; }')
    (tmp_path / 'kiosk-themes' / 'Bad Name.css').write_text('x')
    client = make()
    names = [t['value'] for t in client.get('/api/v1/kiosk_standard/themes').json()]
    assert names == ['candy', 'day', 'meadow', 'my-theme', 'night']
    assert client.get('/api/v1/kiosk_standard/themes').json()[3]['label'] == 'My theme'
    css = client.get('/api/v1/kiosk_standard/themes/night.css')
    assert css.headers['content-type'].startswith('text/css') and 'light' in css.text
    assert '--kiosk-accent' in client.get('/api/v1/kiosk_standard/themes/day.css').text
    assert client.get('/api/v1/kiosk_standard/themes/nope.css').status_code == 404
    assert client.get('/api/v1/kiosk_standard/themes/night').status_code == 404


def test_standard_app_settings_have_defaults(kiosk):
    make, _, _ = kiosk
    client = make()
    values = client.get('/api/v1/settings/modules/kiosk_standard').json()['values']
    assert values['theme'] == 'night' and values['text_size'] == 'large' and values['show_music'] is True
