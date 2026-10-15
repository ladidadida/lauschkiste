from lauschkiste_cli import debug


def test_monotonic_seconds():
    assert debug.monotonic_seconds('ActiveEnterTimestampMonotonic=48246000\n') == 48.246
    assert debug.monotonic_seconds('ActiveEnterTimestampMonotonic=0\n') is None
    assert debug.monotonic_seconds('') is None


def test_process_starts_finds_the_screen_processes():
    ps = "  120 Xorg\n   60 chromium\n   300 sshd\n   bad line\n"
    assert debug.process_starts(ps, 200.0) == [(80.0, 'Xorg'), (140.0, 'chromium')]


def test_boot_prints_the_events_in_order(monkeypatch, capsys):
    monkeypatch.setattr(debug, '_run', lambda *command: '')
    monkeypatch.setattr(debug, '_uptime', lambda: 100.0)
    monkeypatch.setattr(debug, 'boot_events', lambda: [(10.0, 'network online'), (30.5, 'Lauschkiste ready')])
    debug.boot()
    out = capsys.readouterr().out
    assert out.index('network online') < out.index('Lauschkiste ready') < out.index('now')
