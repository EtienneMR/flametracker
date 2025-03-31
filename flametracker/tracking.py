from time import perf_counter
from typing import Optional

from flametracker.types import Tracker


class ActionNode:
    """
    Represents a single action or event in the tracker, including its timing,
    arguments, result, and child actions.
    """

    __slots__ = (
        "tracker",
        "parent",
        "group",
        "start",
        "end",
        "args",
        "kargs",
        "result",
        "children",
    )

    def __init__(
        self,
        tracker: "Tracker",
        parent: Optional["ActionNode"],
        group: str,
        args: tuple,
        kargs: dict,
    ):
        self.tracker = tracker
        self.parent = parent
        self.group = group
        self.start = 0.0
        self.end = 0.0
        self.args = args
        self.kargs = kargs
        self.result = ()
        self.children: list["ActionNode"] = []

        if parent:
            parent.children.append(self)

    @property
    def length(self) -> float:
        """
        Calculates the duration of the action in milliseconds.

        Returns:
            The duration of the action.
        """
        return (self.end - self.start) * 1000

    def set_result(self, result):
        """
        Sets the result of the action.

        Args:
            result: The result to set.
        """
        self.result = result

    def __enter__(self):
        """
        Starts timing the action and sets it as the current node in the tracker.
        """
        assert (
            self.tracker.current == self.parent
        ), "Tracker's current node does not match the parent node"
        assert self.start == 0.0, "ActionNode has already been started"
        self.start = perf_counter()
        self.tracker.current = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Stops timing the action and reverts the current node in the tracker.
        """
        assert (
            self.tracker.current == self
        ), "Tracker's current node does not match this node"
        self.end = perf_counter()
        self.tracker.current = self.parent

    @staticmethod
    def as_event(
        tracker: "Tracker",
        parent: Optional["ActionNode"],
        group: str,
        args: tuple,
        kargs: dict,
        result,
    ):
        """
        Creates an event node without timing.

        Args:
            tracker: The tracker instance.
            parent: The parent action node.
            group: The name of the event.
            args: Positional arguments for the event.
            kargs: Keyword arguments for the event.
            result: The result of the event.

        Returns:
            An ActionNode instance representing the event.
        """
        assert (
            tracker.current == parent
        ), "Tracker's current node does not match the parent node."

        action = ActionNode(tracker, parent, group, args, kargs)
        action.start, action.end = -1.0, -1.0
        action.set_result(result)
        return action
