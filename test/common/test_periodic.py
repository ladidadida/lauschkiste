import threading

from lauschkiste.common.periodic import PeriodicThread


def test_calls_until_closed_and_survives_errors():
    calls = []
    enough = threading.Event()

    def work():
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError('boom')
        enough.set()

    periodic = PeriodicThread('test', 0.01, work)
    periodic.start()
    assert enough.wait(2)
    periodic.close()
    periodic.timer_thread.join(2)
    assert not periodic.timer_thread.is_alive()
    assert len(calls) >= 2
