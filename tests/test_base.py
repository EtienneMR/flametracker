from collections import Counter
from time import sleep

import pytest

from flametracker import Tracker


def test_action_node_timing():
    tracker = Tracker()
    with tracker:
        with tracker.action("test_action") as action:
            sleep(0.1)
            action.set_result("done")

    assert 90 <= action.length <= 110  # Allowing small timing variations
    assert action.result == "done"


def test_tracker_nesting():
    tracker = Tracker()
    with tracker:
        with tracker.action("parent_action") as parent:
            with tracker.action("child_action") as child:
                sleep(0.05)
                child.set_result("child_done")
            parent.set_result("parent_done")

    assert len(parent.children) == 1
    assert parent.children[0].group == "child_action"
    assert 40 <= parent.children[0].length <= 60


def test_render_node_to_dict():
    tracker = Tracker()
    with tracker:
        with tracker.action("test_render") as action:
            sleep(0.05)
            action.set_result("rendered")

    render_node = tracker.to_render(0.01, False)
    render_dict = render_node.to_dict()
    assert isinstance(render_dict, dict)
    assert "name" in render_dict
    assert "length" in render_dict
    assert "children" in render_dict


def test_tracker_to_flamegraph():
    tracker = Tracker()
    with tracker:
        with tracker.action("flamegraph_action"):
            sleep(0.05)

    flamegraph = tracker.to_flamegraph()
    assert "<!DOCTYPE html>" in flamegraph
    assert "flamegraph_action" in flamegraph


def test_tracker_wrap_decorator():
    tracker = Tracker()

    @tracker.wrap
    def sample_function(x):
        return x * 2

    with tracker:
        result = sample_function(5)

    assert result == 10
    assert tracker.root.children[0].group == "sample_function"
    assert tracker.root.children[0].result == 10
