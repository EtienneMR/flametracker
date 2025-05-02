from time import sleep

from flametracker import Tracker, action, wrap
from flametracker.tracking import ActionNode


def test_action_node_timing():
    with Tracker() as tracker:
        with tracker.action("test_action") as action:
            sleep(0.1)
            action.set_result("done")

    assert 90 <= action.length  # Allowing small timing variations
    assert action.result == "done"


def test_tracker_nesting():
    with Tracker() as tracker:
        with tracker.action("parent_action") as parent:
            with tracker.action("child_action") as child:
                sleep(0.05)
                child.set_result("child_done")
            parent.set_result("parent_done")

    assert len(parent.children) == 1
    assert parent.children[0].group == "child_action"
    assert 40 <= parent.children[0].length


def test_render_node_to_dict():
    with Tracker() as tracker:
        with tracker.action("test_render") as action:
            sleep(0.05)
            action.set_result("rendered")

    render_node = tracker.to_render(0.01, None)
    render_dict = render_node.to_dict()
    assert isinstance(render_dict, dict)
    assert "name" in render_dict
    assert "length" in render_dict
    assert "children" in render_dict


def test_tracker_to_flamegraph():
    with Tracker() as tracker:
        with tracker.action("flamegraph_action"):
            sleep(0.05)

    flamegraph = tracker.to_flamegraph()
    assert "<!DOCTYPE html>" in flamegraph
    assert "flamegraph_action" in flamegraph


def test_active_tracker():
    tracker = Tracker()

    assert not tracker.is_active()
    assert Tracker._active_tracker is None
    with tracker:
        assert tracker.is_active()
        assert Tracker._active_tracker == tracker
    assert not tracker.is_active()
    assert Tracker._active_tracker is None


def test_tracker_action_function():
    tracker = Tracker()

    assert not isinstance(action("test_action"), ActionNode)
    with tracker:
        assert isinstance(action("test_action"), ActionNode)
        assert action("test_action").group == "test_action"
    assert not isinstance(action("test_action"), ActionNode)


def test_tracker_wrap_decorator():
    @wrap
    def sample_function(x):
        return x * 2

    with Tracker() as tracker:
        result = sample_function(5)

    assert result == 10
    assert (
        tracker.root.children[0].group
        == "test_tracker_wrap_decorator.<locals>.sample_function"
    )
    assert tracker.root.children[0].result == 10


def test_tracker_multiple_children():
    with Tracker() as tracker:
        with tracker.action("parent_action") as parent:
            with tracker.action("child_action_1") as child1:
                sleep(0.02)
                child1.set_result("child1_done")
            with tracker.action("child_action_2") as child2:
                sleep(0.03)
                child2.set_result("child2_done")
            parent.set_result("parent_done")

    assert len(parent.children) == 2
    assert parent.children[0].group == "child_action_1"
    assert parent.children[1].group == "child_action_2"
    assert 20 <= parent.children[0].length
    assert 30 <= parent.children[1].length
    assert 50 <= parent.length


def test_tracker_to_dict_nested():
    with Tracker() as tracker:
        with tracker.action("parent_action") as parent:
            with tracker.action("child_action") as child:
                sleep(0.01)
                child.set_result("child_done")
            parent.set_result("parent_done")

    render_dict = tracker.to_dict(0.01)
    assert render_dict["name"] == "@root() -> ()"
    assert len(render_dict["children"]) == 1
    assert render_dict["children"][0]["name"] == "parent_action() -> 'parent_done'"
    assert len(render_dict["children"][0]["children"]) == 1
    assert (
        render_dict["children"][0]["children"][0]["name"]
        == "child_action() -> 'child_done'"
    )


def test_tracker_to_flamegraph_split():
    with Tracker() as tracker:
        with tracker.action("parent_action") as parent:
            with tracker.action("child_action_1"):
                sleep(0.01)
            with tracker.action("child_action_2"):
                sleep(0.02)
            parent.set_result("parent_done")

    flamegraph = tracker.to_flamegraph(splited=True)
    assert "<!DOCTYPE html>" in flamegraph
    assert "child_action_1" in flamegraph
    assert "child_action_2" in flamegraph


def test_tracker_activate():
    try:
        tracker = Tracker()

        tracker.activate()
        assert tracker.is_active()

        with tracker.action("test_action"):
            assert tracker.is_active()

        assert tracker.try_deactivate()
        assert not tracker.is_active()
    finally:
        Tracker._active_tracker = None


def test_tracker_try_deactivate():
    try:
        tracker = Tracker()
        tracker.activate()

        assert tracker.is_active()
        assert Tracker._active_tracker == tracker

        with tracker.action("test_action"):
            assert tracker.try_deactivate() is False
        assert tracker.is_active()
        assert Tracker._active_tracker is None

        assert tracker.try_deactivate() is True
        assert not tracker.is_active()

        assert tracker.try_deactivate() is False
    finally:
        Tracker._active_tracker = None
