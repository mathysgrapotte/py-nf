"""Small context managers for Nextflow session lifecycle and observer registration.

These helpers exist to keep ``execution.execute_nextflow`` readable and to make
cleanup best-effort even if an exception occurs mid-run.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import jpype


@contextmanager
def managed_session(Session: Any, script_path: str) -> Iterator[Any]:
    """Create, initialize, start, and always destroy a Nextflow session."""
    session = Session()

    ArrayList = jpype.JClass("java.util.ArrayList")
    ScriptFile = jpype.JClass("nextflow.script.ScriptFile")
    script_file = ScriptFile(jpype.java.nio.file.Paths.get(script_path))

    session.init(script_file, ArrayList(), None, None)
    session.start()

    try:
        yield session
    finally:
        try:
            session.destroy()
        except Exception:
            # Best effort: do not mask the original exception.
            pass


@contextmanager
def registered_trace_observer(session: Any, observer_proxy: Any) -> Iterator[None]:
    """Register a ``TraceObserverV2`` instance on a session (best-effort removal)."""
    observers = None
    try:
        field = session.getClass().getDeclaredField("observersV2")
        field.setAccessible(True)
        observers = field.get(session)
        observers.add(observer_proxy)
        yield
    finally:
        if observers is None:
            return
        try:
            observers.remove(observer_proxy)
        except Exception:
            pass
