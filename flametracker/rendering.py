from collections import Counter
from json import dumps
from math import floor, log10

from flametracker.types import ActionNode


class RenderNode:
    """
    Represents a rendered view of an action node, including its duration,
    call counts, and child nodes.
    """

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
        use_calls_as_value: "bool|dict",
    ):
        if use_calls_as_value == True:
            use_calls_as_value = {}

        self.group = action.group
        self.length = action.length
        self.action = action
        self.children = children
        self.calls = calls
        self.group_size = 1
        self.use_calls_as_value = use_calls_as_value

    def format_args(self, with_result=True):
        """
        Formats the arguments and result of the action for display.

        Args:
            with_result: Whether to include the result in the output.

        Returns:
            A formatted string of the arguments and result.
        """
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
        """
        Groups this node with another node of the same group.

        Args:
            other: The other RenderNode to group with.
        """
        assert self.action.group == other.action.group
        self.calls.update(other.calls)
        self.scale(1 + other.length / self.length, 1)

    def scale(self, length_factor: float, group_add: int):
        """
        Scales the duration and group size of this node and its children.

        Args:
            length_factor: The factor by which to scale the duration.
            group_add: The number of groups to add.
        """
        self.length *= length_factor
        self.group_size += group_add
        for child in self.children:
            child.scale(length_factor, self.group_size)

    def get_value(self):
        """
        Calculates the value of this node based on its duration or call counts.

        Returns:
            The calculated value.
        """
        if self.use_calls_as_value != False:
            return sum(
                calls * self.use_calls_as_value.get(group, 1)
                for group, calls in self.calls.items()
            )
        else:
            return self.length

    def to_dict(self) -> dict:
        """
        Converts this node and its children into a dictionary representation.

        Returns:
            A dictionary representation of this node.
        """
        length_decimal_places = -floor(
            min(log10(self.length) if self.length != 0 else 0, -2)
        )

        return {
            "name": self.group
            + (self.format_args() if self.group_size == 1 else f" x{self.group_size}"),
            "length": f"{self.length:.{length_decimal_places}f}",
            "value": self.get_value(),
            "calls": self.calls,
            "children": [child.to_dict() for child in self.children],
        }

    def to_str(self, ignore_args):
        """
        Converts this node and its children into a string representation.

        Args:
            ignore_args: Whether to ignore arguments in the output.

        Returns:
            A string representation of this node.
        """
        args = "" if ignore_args else self.format_args(False)
        result = "" if ignore_args else " " + repr(self.action.result)

        if self.children:
            lines = []
            lines.append(
                self.group + (args if self.group_size == 1 else f" x{self.group_size}")
            )

            for child in self.children:
                for line in child.to_str(ignore_args).split("\n"):
                    lines.append("│ " + line)

            lines.append(f"╰─>{result} {self.length:.2f}ms {repr(dict(self.calls))}")

            return "\n".join(lines)
        else:
            return (
                self.group
                + (args + " ─>" + result if self.group_size == 1 else f" x{self.group_size}")
                + f" {self.length:.2f}ms"
            )

    def to_flamegraph(self, splited):
        """
        Converts this node and its children into a flamegraph HTML representation.

        Args:
            splited: Whether to split the flamegraph by root children.

        Returns:
            A string containing the flamegraph HTML.
        """
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

      function label(d) {return `${d.data.name}\nlength: ${d.data.length}ms\ncalls: ${JSON.stringify(d.data.calls, null, 2)}`}
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
            dumps(data, check_circular=False, sort_keys=True),
        )

    @staticmethod
    def from_action(
        action: "ActionNode", group_min_time: float, use_calls_as_value: "bool|dict"
    ) -> "RenderNode":
        """
        Creates a RenderNode from an ActionNode.

        Args:
            action: The ActionNode to render.
            group_min_time: Minimum time to group actions.
            use_calls_as_value: Whether to use call counts as values.

        Returns:
            A RenderNode instance.
        """
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
