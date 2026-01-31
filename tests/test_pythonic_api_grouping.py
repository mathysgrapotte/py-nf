"""Tests for pythonic nf-core API keyword grouping.

These tests do not execute Nextflow. They validate that the grouping logic
maps keyword arguments to the correct input groups (or raises on ambiguity).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import pynf


def test_run_module_groups_single_channel(monkeypatch, tmp_path: Path) -> None:
    # One channel with two params.
    monkeypatch.setattr(
        pynf.api,
        "get_module_inputs",
        lambda *a, **k: [{"type": "tuple", "params": [{"name": "meta"}, {"name": "reads"}]}],
    )

    class DummyRaw:
        def get_output_files(self):
            return ["/tmp/out.txt"]

        def get_workflow_outputs(self):
            return [{"name": "x", "value": 1, "index": 0}]

        def get_execution_report(self):
            return {"completed_tasks": 1}

    monkeypatch.setattr(pynf, "run_nfcore_module", lambda *a, **k: DummyRaw())

    res = pynf.run_module("fastqc", meta={"id": "s1"}, reads=["a.fq"])
    assert res.output_files == ["/tmp/out.txt"]


def test_run_module_raises_on_unknown_kw(monkeypatch) -> None:
    monkeypatch.setattr(
        pynf.api,
        "get_module_inputs",
        lambda *a, **k: [{"type": "tuple", "params": [{"name": "meta"}]}],
    )
    monkeypatch.setattr(pynf, "run_nfcore_module", lambda *a, **k: None)

    with pytest.raises(ValueError):
        pynf.run_module("fastqc", meta={"id": "s1"}, DOES_NOT_EXIST=123)


def test_run_module_raises_on_ambiguity(monkeypatch) -> None:
    # Two channels both accept 'meta' -> ambiguous if user only supplies meta.
    monkeypatch.setattr(
        pynf.api,
        "get_module_inputs",
        lambda *a, **k: [
            {"type": "tuple", "params": [{"name": "meta"}]},
            {"type": "tuple", "params": [{"name": "meta"}]},
        ],
    )
    monkeypatch.setattr(pynf, "run_nfcore_module", lambda *a, **k: None)

    with pytest.raises(ValueError):
        pynf.run_module("whatever", meta={"id": "s1"})
