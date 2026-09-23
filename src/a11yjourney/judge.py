"""The semantic judge: the swappable brain of the engine.

Structural checks answer "is a label present". The judge answers the harder,
higher-value question, "is it *meaningful*", and reasons about focus order and
task completion. That judgment is what static scanners cannot do.

Three implementations ship here:

* :class:`HeuristicJudge` - zero-dependency default. Fast, offline, approximate.
* :class:`ModelJudge` - wraps any callable ``complete(prompt) -> str`` so a real
  language model makes the call. Vendor-neutral.
* :func:`make_judge` - a factory that builds a live model judge from environment
  variables (Anthropic or any OpenAI-compatible endpoint), using only the
  standard library, and falls back to the heuristic when no key is present.

No third-party packages are required; provider calls use ``urllib``.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from collections.abc import Callable
from typing import Protocol, runtime_checkable

from .model import Node

_GENERIC = re.compile(r"^(button\d*|btn[_-]?\d*|image\d*|icon\d*|label\d*|view\d*|untitled)$", re.I)
_FILENAME = re.compile(r"\.(png|jpg|jpeg|webp|svg|gif)$", re.I)

_PROMPT = (
    "You audit a native mobile screen for a user who relies on a screen reader.\n"
    "Element role: {role}\n"
    "Programmatic accessible name: {label!r}\n"
    "Other visible text on the screen: {context}\n\n"
    "Question: is this accessible name meaningful and sufficient for a "
    "screen-reader user to understand what this element is or does? "
    "A name like 'button1', an image filename, or an empty name is NOT "
    "meaningful. Reply with exactly one word: PASS or FAIL."
)


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
    """Use a real model for the semantic judgment.

    ``complete`` is any callable taking a prompt and returning the model's text.
    Results are cached per (role, label, context) so repeated elements and
    re-runs do not re-bill the model. If the model errors or replies oddly, we
    fail safe by deferring to the heuristic, so a bad call never crashes a run.
    """

    def __init__(self, complete: Callable[[str], str]) -> None:
        self._complete = complete
        self._cache: dict[tuple[str, str, str], bool] = {}
        self._fallback = HeuristicJudge()

    def label_meaningful(self, node: Node, context: list[str]) -> bool:
        key = (node.cls, node.name, " | ".join(context[:8]))
        if key in self._cache:
            return self._cache[key]
        prompt = _PROMPT.format(role=node.cls or "unknown", label=node.name,
                                context=", ".join(context[:8]) or "(none)")
        try:
            verdict = self._complete(prompt).strip().upper()
            result = verdict.startswith("PASS")
            if not (verdict.startswith("PASS") or verdict.startswith("FAIL")):
                result = self._fallback.label_meaningful(node, context)
        except Exception:
            result = self._fallback.label_meaningful(node, context)
        self._cache[key] = result
        return result


# --------------------------------------------------------------------------
# Live provider adapters (standard library only). Return a `complete` callable.
# --------------------------------------------------------------------------

def _http_json(url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
    body = json.dumps(payload).encode()
    all_headers = {"Content-Type": "application/json", **headers}
    req = urllib.request.Request(url, data=body, headers=all_headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        loaded: dict[str, object] = json.loads(resp.read())
        return loaded


def anthropic_completer(
    api_key: str, model: str = "claude-3-5-haiku-latest"
) -> Callable[[str], str]:
    """A `complete` backed by the Anthropic Messages API."""

    def complete(prompt: str) -> str:
        data = _http_json(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            {"model": model, "max_tokens": 8, "messages": [{"role": "user", "content": prompt}]},
        )
        content = data.get("content", [])
        parts = content if isinstance(content, list) else []
        return "".join(str(b.get("text", "")) for b in parts if isinstance(b, dict))

    return complete


def openai_completer(
    api_key: str, model: str = "gpt-4o-mini", base_url: str = "https://api.openai.com/v1"
) -> Callable[[str], str]:
    """A `complete` backed by any OpenAI-compatible chat-completions endpoint."""

    def complete(prompt: str) -> str:
        data = _http_json(
            base_url.rstrip("/") + "/chat/completions",
            {"Authorization": f"Bearer {api_key}"},
            {"model": model, "max_tokens": 8, "messages": [{"role": "user", "content": prompt}]},
        )
        choices = data["choices"]
        return str(choices[0]["message"]["content"])  # type: ignore[index]

    return complete


def make_judge(kind: str = "auto") -> Judge:
    """Build a judge.

    ``kind``:
      * ``heuristic`` - always the offline heuristic.
      * ``model`` - a live model judge; raises if no provider is configured.
      * ``auto`` (default) - a model judge if an API key is in the environment,
        otherwise the heuristic.

    Environment:
      * ``ANTHROPIC_API_KEY`` (+ optional ``A11YJOURNEY_MODEL``), or
      * ``OPENAI_API_KEY`` (+ optional ``A11YJOURNEY_MODEL``, ``OPENAI_BASE_URL``).
    """
    if kind == "heuristic":
        return HeuristicJudge()

    model = os.environ.get("A11YJOURNEY_MODEL")
    if os.environ.get("ANTHROPIC_API_KEY"):
        completer = anthropic_completer(
            os.environ["ANTHROPIC_API_KEY"], model or "claude-3-5-haiku-latest"
        )
        return ModelJudge(completer)
    if os.environ.get("OPENAI_API_KEY"):
        completer = openai_completer(
            os.environ["OPENAI_API_KEY"], model or "gpt-4o-mini",
            os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        return ModelJudge(completer)

    if kind == "model":
        raise RuntimeError(
            "judge=model requested but no ANTHROPIC_API_KEY or OPENAI_API_KEY is set."
        )
    return HeuristicJudge()
