import pytest
from ops.charm import CharmBase, CharmEvents, StartEvent
from ops.framework import CommitEvent, EventBase, EventSource, PreCommitEvent

from scenario import Event, State
from scenario.capture_events import capture_events
from tests.helpers import trigger


class Foo(EventBase):
    pass


class MyCharmEvents(CharmEvents):
    foo = EventSource(Foo)


class MyCharm(CharmBase):
    META = {"name": "mycharm"}
    on = MyCharmEvents()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.foo, self._on_foo)

    def _on_start(self, e):
        self.on.foo.emit()

    def _on_foo(self, e):
        pass


def test_capture_custom_evt():
    with capture_events(Foo) as emitted:
        trigger(State(), "foo", MyCharm, meta=MyCharm.META)

    assert len(emitted) == 1
    assert isinstance(emitted[0], Foo)


def test_capture_custom_evt_nonspecific_capture():
    with capture_events() as emitted:
        trigger(State(), "foo", MyCharm, meta=MyCharm.META)

    assert len(emitted) == 1
    assert isinstance(emitted[0], Foo)


def test_capture_custom_evt_nonspecific_capture_include_fw_evts():
    with capture_events(include_framework=True) as emitted:
        trigger(State(), "foo", MyCharm, meta=MyCharm.META)

    assert len(emitted) == 3
    assert isinstance(emitted[0], Foo)
    assert isinstance(emitted[1], PreCommitEvent)
    assert isinstance(emitted[2], CommitEvent)


def test_capture_juju_evt():
    with capture_events() as emitted:
        trigger(State(), "start", MyCharm, meta=MyCharm.META)

    assert len(emitted) == 2
    assert isinstance(emitted[0], StartEvent)
    assert isinstance(emitted[1], Foo)


def test_capture_deferred_evt():
    # todo: this test should pass with ops < 2.1 as well
    with capture_events() as emitted:
        trigger(
            State(deferred=[Event("foo").deferred(handler=MyCharm._on_foo)]),
            "start",
            MyCharm,
            meta=MyCharm.META,
        )

    assert len(emitted) == 3
    assert isinstance(emitted[0], Foo)
    assert isinstance(emitted[1], StartEvent)
    assert isinstance(emitted[2], Foo)


def test_capture_no_deferred_evt():
    # todo: this test should pass with ops < 2.1 as well
    with capture_events(include_deferred=False) as emitted:
        trigger(
            State(deferred=[Event("foo").deferred(handler=MyCharm._on_foo)]),
            "start",
            MyCharm,
            meta=MyCharm.META,
        )

    assert len(emitted) == 2
    assert isinstance(emitted[0], StartEvent)
    assert isinstance(emitted[1], Foo)
