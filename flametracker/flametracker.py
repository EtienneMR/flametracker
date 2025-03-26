import json
import math
from collections import Counter
from functools import wraps
from time import perf_counter
from typing import Callable, Optional, TypeVar, cast

F = TypeVar("F", bound=Callable)


class _UntrackedActionNode:
    def set_result(self, result):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ActionNode:
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
        return (self.end - self.start) * 1000

    def set_result(self, result):
        self.result = result

    def __enter__(self):
        assert self.tracker.current == self.parent
        self.start = perf_counter()
        self.tracker.current = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.tracker.current == self
        self.end = perf_counter()
        self.tracker.current = self.parent


class RenderNode:
    __slots__ = (
        "avg_action_time",
        "group",
        "length",
        "action",
        "children",
        "calls",
        "group_size",
        "use_calls_as_value",
    )

    def __init__(
        self,
        action: "ActionNode",
        calls: "Counter[str]",
        children: "list[RenderNode]",
        use_calls_as_value: bool,
    ):
        self.avg_action_time = action.tracker.avg_action_time
        self.group = action.group
        self.length = action.length
        self.action = action
        self.children = children
        self.calls = calls
        self.group_size = 1
        self.use_calls_as_value = use_calls_as_value

    def format_args(self, with_result=True):
        return (
            "("
            + ", ".join(
                [repr(arg) for arg in self.action.args]
                + [f"{key}={repr(value)}" for key, value in self.action.kargs.items()]
            )
            + ")"
            + (f" -> {repr(self.action.result)}" if with_result else "")
        )

    def group_with(self, other: "RenderNode"):
        assert self.action.group == other.action.group
        self.calls.update(other.calls)
        self.scale(1 + other.length / self.length, 1)

    def get_representative(self):
        return min(self.length / self.avg_action_time / self.group_size / 10, 1)

    def scale(self, length_factor: float, group_add: int):
        self.length *= length_factor
        self.group_size += group_add
        for child in self.children:
            child.scale(length_factor, self.group_size)

    def to_dict(self) -> dict:
        length_decimal_places = -math.floor(
            min(math.log10(self.length) if self.length != 0 else 0, -2)
        )

        return {
            "name": self.group
            + (self.format_args() if self.group_size == 1 else f" x{self.group_size}"),
            "length": f"{self.length:.{length_decimal_places}f}",
            "value": self.calls.total() if self.use_calls_as_value else self.length,
            "representative": self.get_representative(),
            "calls": self.calls,
            "children": [child.to_dict() for child in self.children],
        }

    def to_str(self, ignore_args):
        args = "" if ignore_args else self.format_args(False)
        result = "" if ignore_args else " " + repr(self.action.result)

        if self.children:
            lines = []
            lines.append(
                self.group + (args if self.group_size == 1 else f" x{self.group_size}")
            )

            for child in self.children:
                for line in child.to_str(ignore_args).split("\n"):
                    lines.append("| " + line)

            lines.append(f"\\ ->{result} {self.length:.2f}ms {repr(dict(self.calls))}")

            return "\n".join(lines)
        else:
            return (
                self.group
                + (args if self.group_size == 1 else f" x{self.group_size}")
                + f" {self.length:.2f}ms"
            )

    def to_flamegraph(self, splited):
        base = """<!DOCTYPE html>
<html>
  <head>
    <title>flametracker - flamegraph</title>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width" />
    <script>const data = /*data*/ [];</script>
  <body>
    <pre id="details"></pre>
    <script type="module">
      import {select} from "https://cdn.jsdelivr.net/npm/d3-selection@3.0.0/+esm";
      import {flamegraph} from "https://cdn.jsdelivr.net/npm/d3-flame-graph@4.1.3/+esm"
      import style from "https://cdn.jsdelivr.net/npm/d3-flame-graph@4.1.3/dist/d3-flamegraph.css" with {type: "css"}
      style.insertRule("body {margin: 0; min-width: 960px; min-height: 100vh; display: flex; align-items: center; flex-wrap: wrap; justify-content: center}", 0)
      style.insertRule("#details {width: 960px; height: 240px; padding: 5px; overflow-x: auto; background: white}")
      document.adoptedStyleSheets.push(style)

      const details = document.getElementById("details")

      function label(d) {return `${d.data.name}\nlength: ${d.data.length}ms (${d.data.representative > 0.5 ? '' : '⚠️ '}${d.data.representative*100}%)\ncalls: ${JSON.stringify(d.data.calls, null, 2)}`}
      function detailsHandler(d) {if (d) {details.textContent = d}}

      for (const graph of data) {
        const graphDiv = document.createElement("div")

        select(graphDiv)
          .datum(graph)
          .call(
            flamegraph()
              .sort(false)
              .label(label)
              .setDetailsHandler(detailsHandler)
          );

        document.body.insertBefore(graphDiv, details)
      }
    </script>
  </body>
</html>"""
        root = self.to_dict()
        if splited:
            data = []
            for child in root["children"]:
                rooted = root.copy()
                rooted["children"] = [child]
                data.append(rooted)
        else:
            data = [root]

        return base.replace(
            "/*data*/ []",
            json.dumps(data, check_circular=False, sort_keys=True),
        )

    @staticmethod
    def from_action(
        action: "ActionNode", group_min_time: float, use_calls_as_value: bool
    ) -> "RenderNode":
        children = [
            RenderNode.from_action(child, group_min_time, use_calls_as_value)
            for child in action.children
        ]

        calls = Counter((action.group,))

        grouped_children: "list[RenderNode]" = []
        group_buffer: "RenderNode|None" = None

        for child in children:
            calls.update(child.calls)

            if use_calls_as_value or group_min_time == 0:
                grouped_children.append(child)
            elif child.length > group_min_time:
                if group_buffer:
                    grouped_children.append(group_buffer)
                    group_buffer = None
                grouped_children.append(child)
            elif group_buffer and group_buffer.group == child.group:
                group_buffer.group_with(child)
                if group_buffer.length > group_min_time:
                    grouped_children.append(group_buffer)
                    group_buffer = None
            else:
                if group_buffer:
                    grouped_children.append(group_buffer)
                group_buffer = child

        if group_buffer:
            grouped_children.append(group_buffer)

        return RenderNode(action, calls, grouped_children, use_calls_as_value)


class Tracker:
    UntrackedActionNode = _UntrackedActionNode()
    active_tracker: Optional["Tracker"] = None

    def __init__(self, action_benchmark_repeat: int = 10**6):
        self.root = ActionNode(self, None, "@root", (), {})
        self.current = None

        if action_benchmark_repeat > 0:
            start = perf_counter()
            with Tracker(0):
                for _ in range(action_benchmark_repeat):
                    with Tracker.action("test"):
                        pass
            end = perf_counter()
            self.avg_action_time = (end - start) / action_benchmark_repeat * 1000
        else:
            self.avg_action_time = 0

    def __enter__(self):
        assert self.active_tracker is None
        Tracker.active_tracker = self
        self.root.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.active_tracker == self
        self.root.__exit__(exc_type, exc_val, exc_tb)
        Tracker.active_tracker = None

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

    @staticmethod
    def action(name: str, *args, **kargs):
        tracker = Tracker.active_tracker
        if tracker:
            action = ActionNode(tracker, tracker.current, name, args, kargs)
            return action
        else:
            return Tracker.UntrackedActionNode

    @staticmethod
    def wrap(fn: F) -> F:
        @wraps(fn)
        def call(*args, **kargs):
            tracker = Tracker.active_tracker
            if tracker:
                with tracker.action(fn.__name__, *args, **kargs) as action:
                    result = fn(*args, **kargs)
                    action.set_result(result)
                    return result
            else:
                return fn(*args, **kargs)

        return cast(F, call)
