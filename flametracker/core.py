from functools import wraps
from typing import cast

from flametracker.rendering import RenderNode
from flametracker.tracking import ActionNode
from flametracker.types import F

from . import UntrackedActionNode


class Tracker:
    _active_tracker: "Tracker|None" = None

    def __init__(self):
        if not __debug__:
            raise RuntimeError("Tracker is disabled in optimized mode")

        self.root = ActionNode(self, None, "@root", (), {})
        self.current = None

    def __enter__(self):
        assert Tracker._active_tracker is None
        Tracker._active_tracker = self
        self.root.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.is_active()
        self.root.__exit__(exc_type, exc_val, exc_tb)
        Tracker._active_tracker = None

    def is_active(self):
        return self.current is not None

    def activate(self):
        self.__enter__()

    def try_deactivate(self):
        assert Tracker._active_tracker in (self, None)
        Tracker._active_tracker = None

        if self.current == self.root:
            self.root.__exit__(None, None, None)
            return True

        return False

    def to_render(self, group_min_percent: float, use_calls_as_value: bool):
        return RenderNode.from_action(
            self.root, group_min_percent * self.root.length, use_calls_as_value
        )

    def to_dict(self, group_min_percent: float = 0.01, use_calls_as_value=False):
        return self.to_render(group_min_percent, use_calls_as_value).to_dict()

    def to_str(self, group_min_percent: float = 0.1, ignore_args: bool = False):
        return self.to_render(group_min_percent, True).to_str(ignore_args)

    def to_flamegraph(
        self, group_min_percent: float = 0.01, splited=False, use_calls_as_value=False
    ):
        return self.to_render(group_min_percent, use_calls_as_value).to_flamegraph(
            splited,
        )

    def action(self, name: str, *args, **kargs):
        return ActionNode(self, self.current, name, args, kargs)

    def event(self, name: str, *args, result=None, **kargs):
        return ActionNode.as_event(self, self.current, name, args, kargs, result)


def action(name: str, *args, **kargs):
    if not __debug__:
        return UntrackedActionNode

    return (
        Tracker._active_tracker.action(name, *args, **kargs)
        if Tracker._active_tracker
        else UntrackedActionNode
    )


def event(name: str, *args, result=None, **kargs):
    if not __debug__:
        return UntrackedActionNode

    return (
        Tracker._active_tracker.event(name, *args, result=result**kargs)
        if Tracker._active_tracker
        else UntrackedActionNode
    )


def wrap(fn: F) -> F:
    if not __debug__:
        return fn

    @wraps(fn)
    def call(*args, **kargs):
        tracker = Tracker._active_tracker
        if tracker:
            with tracker.action(fn.__qualname__, *args, **kargs) as action:
                result = fn(*args, **kargs)
                action.set_result(result)
                return result
        else:
            return fn(*args, **kargs)

    return cast(F, call)
