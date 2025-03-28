from typing import TYPE_CHECKING, Callable, TypeVar

if TYPE_CHECKING:
    from .core import Tracker
    from .rendering import RenderNode
    from .tracking import ActionNode

    F = TypeVar("F", bound=Callable)
else:
    Tracker = None
    RenderNode = None
    ActionNode = None
    F = None
