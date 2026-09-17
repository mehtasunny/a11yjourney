"""The semantic judge.

Structural checks answer "is a label present". The judge answers the harder,
higher-value question: "is it *meaningful*". In production this is a language
or vision model. The :class:`HeuristicJudge` is a zero-dependency default so
the tool runs anywhere; implement :class:`Judge` to plug in a real model.
"""
from __future__ import annotations

import re
from collections.abc import Callable
from typing import Protocol, runtime_checkable

from .model import Node

_GENERIC = re.compile(r"^(button\d*|btn[_-]?\d*|image\d*|icon\d*|label\d*|view\d*|untitled)$", re.I)
_FILENAME = re.compile(r"\.(png|jpg|jpeg|webp|svg|gif)$", re.I)


@runtime_checkable
class Judge(Protocol):
    """Contract for a semantic judge. Return True when a label is meaningful."""

    def label_meaningful(self, node: Node, context: list[str]) -> bool: ...


class HeuristicJudge:
    """Dependency-free default. Documents exactly where a model would decide."""

    def label_meaningful(self, node: Node, context: list[str]) -> bool:
        name = (node.name or "").strip()
        if not name:
            return False
        return not (_GENERIC.match(name) or _FILENAME.search(name))


class ModelJudge:
    """Adapter for a real LLM/VLM. Vendor-neutral by design.

    Pass any callable that takes a prompt string and returns the model's text.
    Wire your provider's client into `complete` and this becomes the semantic
    core described in the architecture. Kept out of the default path so the
    library has zero required dependencies.
    """

    PROMPT = (
        "You audit a mobile screen for a blind user. Element role: {role}. "
        "Programmatic label: {label!r}. Nearby visible text: {context}. "
        "Is this label meaningful and sufficient for a screen-reader user to "
        "know what this control does? Answer strictly PASS or FAIL."
    )

    def __init__(self, complete: Callable[[str], str]) -> None:
        self._complete = complete

    def label_meaningful(self, node: Node, context: list[str]) -> bool:
        prompt = self.PROMPT.format(role=node.cls, label=node.name, context=", ".join(context[:8]))
        return self._complete(prompt).strip().upper().startswith("PASS")
