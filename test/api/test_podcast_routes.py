from unittest.mock import Mock

import pytest

import lauschkiste.podcasts
import lauschkiste.resume
from lauschkiste.podcasts import FeedError, parse_feed

RSS = b'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Kakadu</title>
    <itunes:image href="https://example.org/kakadu.jpg"/>
    <item>
      <title>Older</title>
      <guid>ep-1</guid>
      <pubDate>Mon, 01 Sep 2026 07:00:00 +0200</pubDate>
      <itunes:duration>12:30</itunes:duration>
      <enclosure url="https://example.org/1.mp3" type="audio/mpeg" length="1"/>
    </item>
    <item>
      <title>Newer</title>
      <guid>ep-2</guid>
      <pubDate>Mon, 08 Sep 2026 07:00:00 +0200</pubDate>
      <itunes:duration>1:00:05</itunes:duration>
      <enclosure url="https://example.org/2.mp3" type="audio/mpeg" length="1"/>
    </item>
    <item><title>No audio</title></item>
  </channel>
</rss>'''

ATOM = b'''<feed xmlns="http://www.w3.org/2005/Atom"><title>Atom cast</title>
<entry><id>a1</id><title>One</title><published>2026-09-01T10:00:00Z</published>
<link rel="enclosure" href="https://example.org/a1.ogg"/></entry></feed>'''


def test_parse_rss():
    feed = parse_feed(RSS)
    assert (feed['title'], feed['image']) == ('Kakadu', 'https://example.org/kakadu.jpg')
    assert [(e['title'], e['url'], e['duration']) for e in feed['episodes']] == [
        ('Newer', 'https://example.org/2.mp3', 3605.0), ('Older', 'https://example.org/1.mp3', 750.0)]
    assert feed['episodes'][0]['published'] == '2026-09-08T05:00:00+00:00'
    assert len(feed['episodes'][0]['id']) == 12


def test_parse_atom():
    feed = parse_feed(ATOM)
    assert feed['title'] == 'Atom cast'
    assert [e['url'] for e in feed['episodes']] == ['https://example.org/a1.ogg']


@pytest.mark.parametrize('content', [b'not xml', b'<html><body/></html>'])
def test_parse_rejects_non_feeds(content):
    with pytest.raises(FeedError):
        parse_feed(content)


@pytest.fixture
def podcasts(api_client, mocked_player, tmp_path, monkeypatch):
    monkeypatch.setattr(lauschkiste.resume, 'ACTIVATION_GRACE_SEC', 0)
    fetch = Mock(side_effect=lambda url: parse_feed(RSS))
    monkeypatch.setattr(lauschkiste.podcasts, 'fetch_feed', fetch)
    ctrl = Mock()
    ctrl.get_active_backend.return_value = 'local_audio'
    ctrl.playerstatus.return_value = {'state': 'stop'}
    config = {'podcasts': {'podcasts_file': str(tmp_path / 'podcasts.yaml'), 'cache_dir': str(tmp_path / 'cache'),
                           'state_file': str(tmp_path / 'positions.json'), 'save_interval_sec': 0}}
    with api_client([mocked_player(ctrl), lauschkiste.podcasts.Podcasts], config) as client:
        yield client, ctrl, fetch, tmp_path


def test_subscribe_list_rename_delete(podcasts):
    client, _, _, tmp_path = podcasts
    response = client.post('/api/v1/podcasts', json={'url': 'https://example.org/feed.xml'})
    assert response.status_code == 201
    podcast = response.json()
    assert (podcast['id'], podcast['name'], podcast['episodes'], podcast['unheard']) == ('kakadu', 'Kakadu', 2, 2)
    assert podcast['image'] == 'https://example.org/kakadu.jpg'
    assert (tmp_path / 'cache' / 'kakadu.json').exists()

    assert client.put('/api/v1/podcasts/kakadu', json={'name': 'Kinder'}).json()['name'] == 'Kinder'
    assert [p['name'] for p in client.get('/api/v1/podcasts').json()] == ['Kinder']
    assert client.delete('/api/v1/podcasts/kakadu').status_code == 204
    assert client.get('/api/v1/podcasts').json() == []
    assert not (tmp_path / 'cache' / 'kakadu.json').exists()


def test_invalid_feeds_are_rejected(podcasts):
    client, _, fetch, _ = podcasts
    assert client.post('/api/v1/podcasts', json={'url': 'ftp://example.org/x'}).status_code == 422
    fetch.side_effect = FeedError('neither an RSS nor an Atom feed')
    assert client.post('/api/v1/podcasts', json={'url': 'https://example.org/page'}).status_code == 422


def test_episodes_use_the_cache_until_stale(podcasts):
    client, _, fetch, _ = podcasts
    client.post('/api/v1/podcasts', json={'url': 'https://example.org/feed.xml'})
    fetch.reset_mock()
    episodes = client.get('/api/v1/podcasts/kakadu/episodes').json()
    assert [e['title'] for e in episodes] == ['Newer', 'Older']
    fetch.assert_not_called()
    client.post('/api/v1/podcasts/refresh', json={})
    fetch.assert_called_once()


def test_stale_feed_falls_back_to_cache(podcasts):
    client, _, fetch, _ = podcasts
    client.post('/api/v1/podcasts', json={'url': 'https://example.org/feed.xml'})
    fetch.side_effect = FeedError('offline')
    assert client.post('/api/v1/podcasts/refresh', json={'podcast': 'kakadu'}).status_code == 204
    assert len(client.get('/api/v1/podcasts/kakadu/episodes').json()) == 2


def test_play_newest_unheard_then_continue(podcasts):
    client, ctrl, _, _ = podcasts
    client.post('/api/v1/podcasts', json={'url': 'https://example.org/feed.xml'})
    newer, older = [e['id'] for e in client.get('/api/v1/podcasts/kakadu/episodes').json()]

    assert client.post('/api/v1/podcasts/play', json={'podcast': 'kakadu'}).status_code == 204
    ctrl.play_files.assert_called_once_with(['https://example.org/2.mp3'], 0, 0.0, True)

    client.post('/api/v1/podcasts/set_heard', json={'podcast': 'kakadu', 'episode': newer})
    ctrl.play_files.reset_mock()
    client.post('/api/v1/podcasts/play', json={'podcast': 'kakadu'})
    ctrl.play_files.assert_called_once_with(['https://example.org/1.mp3'], 0, 0.0, True)

    bus = client.modules.instance('podcasts')._ctx._bus
    bus.publish('player.status', {'state': 'pause', 'file': 'https://example.org/1.mp3', 'elapsed': '300',
                                  'duration': '750'})
    episodes = {e['id']: e for e in client.get('/api/v1/podcasts/kakadu/episodes').json()}
    assert episodes[older]['elapsed'] == 300.0 and episodes[newer]['heard']
    assert client.get('/api/v1/podcasts').json()[0]['unheard'] == 1

    ctrl.play_files.reset_mock()
    bus.publish('player.status', {'state': 'play', 'file': 'music/other.mp3'})
    client.post('/api/v1/podcasts/play', json={'podcast': 'kakadu', 'episode': older})
    ctrl.play_files.assert_called_once_with(['https://example.org/1.mp3'], 0, 290.0, True)


def test_unknown_podcast_or_episode(podcasts):
    client, _, _, _ = podcasts
    assert client.post('/api/v1/podcasts/play', json={'podcast': 'nope'}).status_code == 404
    client.post('/api/v1/podcasts', json={'url': 'https://example.org/feed.xml'})
    assert client.post('/api/v1/podcasts/play', json={'podcast': 'kakadu', 'episode': 'x'}).status_code == 404
