"""Context managers for Nextflow session lifecycle and observer registration."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import AbstractContextManager
from typing import Any


def managed_session(Session: Any, script_path: str) -> AbstractContextManager[Any]: ...

def registered_trace_observer(session: Any, observer_proxy: Any) -> AbstractContextManager[None]: ...
