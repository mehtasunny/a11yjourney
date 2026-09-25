"""A11yJourney: accessibility auditing for native Android apps."""
__version__ = "0.2.1"

from .checks import Audit, audit, run  # noqa: E402
from .findings import Finding  # noqa: E402
from .judge import (  # noqa: E402
    HeuristicJudge,
    Judge,
    ModelJudge,
    anthropic_completer,
    make_judge,
    openai_completer,
)
from .model import Node, Screen, load, parse  # noqa: E402
from .privacy import redact  # noqa: E402
from .reporters import in_scope, summarize, to_json, to_sarif, to_text  # noqa: E402
from .wcag import DEFAULT_PROFILE, PROFILES, Criterion, Profile, Severity, criterion  # noqa: E402

__all__ = [
    "Audit", "audit", "run", "Finding", "HeuristicJudge", "Judge", "ModelJudge",
    "make_judge", "anthropic_completer", "openai_completer", "Node", "Screen", "load",
    "parse", "redact", "in_scope", "summarize", "to_json", "to_sarif", "to_text",
    "DEFAULT_PROFILE", "PROFILES", "Criterion", "Profile", "Severity", "criterion",
    "__version__",
]
