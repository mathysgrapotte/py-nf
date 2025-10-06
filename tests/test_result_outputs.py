from pynf.result import NextflowResult


class _DummySession:
    def getWorkDir(self):
        return None


def test_observer_outputs_preferred(tmp_path):
    produced = tmp_path / "result.txt"
    published = tmp_path / "publish" / "result.txt"

    workflow_events = [
        {
            "name": "main",
            "value": [str(produced)],
            "index": None,
        }
    ]
    file_events = [
        {
            "target": str(published),
            "source": None,
            "labels": None,
        }
    ]

    result = NextflowResult(
        script=None,
        session=_DummySession(),
        loader=None,
        workflow_events=workflow_events,
        file_events=file_events,
    )

    outputs = result.get_output_files()

    assert outputs == [str(produced), str(published)]


def test_workflow_outputs_structure():
    workflow_events = [
        {
            "name": "summary",
            "value": {"count": 3, "samples": ["a", "b"]},
            "index": None,
        }
    ]

    result = NextflowResult(
        script=None,
        session=_DummySession(),
        loader=None,
        workflow_events=workflow_events,
        file_events=[],
    )

    outputs = result.get_workflow_outputs()

    assert outputs == [
        {
            "name": "summary",
            "value": {"count": 3, "samples": ["a", "b"]},
            "index": None,
        }
    ]
