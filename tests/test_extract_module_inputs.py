#!/usr/bin/env python3
"""Tests for extracting input information from a Nextflow module.

This uses the same underlying approach as the runner: start the JVM, parse the
script with Nextflow's ScriptLoader, and extract input channel metadata via
`ScriptMeta`.

The old NextflowEngine wrapper was removed; this test calls the lower-level
helpers directly.
"""

from pathlib import Path

import jpype
import pytest

from pynf.jvm_bridge import load_nextflow_classes, start_jvm_if_needed
from pynf.process_introspection import get_process_inputs
from pynf.runtime_config import assert_nextflow_jar_exists, resolve_nextflow_jar_path


def nextflow_jar_available() -> bool:
    from pynf.runtime_config import resolve_nextflow_jar_path
    jar = resolve_nextflow_jar_path(None)
    return jar.exists()



@pytest.mark.skipif(not nextflow_jar_available(), reason="Nextflow JAR not present; run python setup_nextflow.py")
def test_native_api_input_extraction() -> None:
    script_path = Path("test_nfcore_cache/samtools/view/main.nf")

    jar_path = resolve_nextflow_jar_path(None)
    assert_nextflow_jar_exists(jar_path)
    start_jvm_if_needed(jar_path)

    classes = load_nextflow_classes()
    Session = classes["Session"]
    ScriptLoaderFactory = classes["ScriptLoaderFactory"]
    ScriptMeta = classes["ScriptMeta"]

    ScriptFile = jpype.JClass("nextflow.script.ScriptFile")
    ArrayList = jpype.JClass("java.util.ArrayList")

    session = Session()
    script_file = ScriptFile(jpype.java.nio.file.Paths.get(str(script_path)))
    session.init(script_file, ArrayList(), None, None)
    session.start()

    loader = ScriptLoaderFactory.create(session)
    java_path = jpype.java.nio.file.Paths.get(str(script_path))
    loader.parse(java_path)
    script = loader.getScript()

    inputs = get_process_inputs(loader, script, ScriptMeta)
    assert isinstance(inputs, list)
    assert len(inputs) >= 1

    session.destroy()


if __name__ == "__main__":
    raise SystemExit("Run with pytest")
