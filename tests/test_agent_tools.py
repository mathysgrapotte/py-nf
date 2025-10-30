"""
Manual test script for pynf-agent tools.

This script tests individual agent tools in isolation to verify they work correctly
before testing them with the full agent.

Run with: uv run python tests/test_agent_tools.py
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pynf_agent.tools import (
    ListNFCoreModulesTool,
    ListSubmodulesTool,
    GetModuleInfoTool,
    RunNFModuleTool,
    ListOutputFilesTool,
    ReadFileTool,
    ListDirectoryTool,
)
from pynf_agent.agent import SessionContext


def test_list_modules():
    """Test listing nf-core modules."""
    print("\n" + "=" * 70)
    print("TEST: ListNFCoreModulesTool")
    print("=" * 70)

    tool = ListNFCoreModulesTool()
    result = tool.forward()

    print(result)
    print("\n✓ Test passed")


def test_list_submodules():
    """Test listing submodules."""
    print("\n" + "=" * 70)
    print("TEST: ListSubmodulesTool")
    print("=" * 70)

    tool = ListSubmodulesTool()

    # Test with samtools (has many submodules)
    print("\n[1] Testing samtools submodules:")
    result = tool.forward("samtools")
    print(result)

    # Test with fastqc (no submodules)
    print("\n[2] Testing fastqc submodules:")
    result = tool.forward("fastqc")
    print(result)

    print("\n✓ Test passed")


def test_get_module_info():
    """Test getting module information."""
    print("\n" + "=" * 70)
    print("TEST: GetModuleInfoTool")
    print("=" * 70)

    tool = GetModuleInfoTool()

    # Test with fastqc
    print("\n[1] Getting info for fastqc:")
    result = tool.forward("fastqc")
    print(result)

    print("\n✓ Test passed")


def test_list_directory():
    """Test directory listing."""
    print("\n" + "=" * 70)
    print("TEST: ListDirectoryTool")
    print("=" * 70)

    tool = ListDirectoryTool()

    # Test current directory
    print("\n[1] Listing current directory:")
    result = tool.forward(".")
    print(result)

    print("\n✓ Test passed")


def test_session_context():
    """Test SessionContext."""
    print("\n" + "=" * 70)
    print("TEST: SessionContext")
    print("=" * 70)

    context = SessionContext(working_dir="./test_workspace")

    # Add execution
    print("\n[1] Adding execution record:")
    exec_id = context.add_execution(
        module="fastqc",
        inputs=[{"meta": {"id": "test"}, "reads": ["test.fq"]}],
        outputs=["output1.html", "output2.zip"],
        status="success"
    )
    print(f"  Created execution ID: {exec_id}")

    # Get latest
    print("\n[2] Getting latest execution:")
    latest = context.get_latest_execution()
    print(f"  Module: {latest['module']}")
    print(f"  Status: {latest['status']}")
    print(f"  Outputs: {latest['outputs']}")

    # Get summary
    print("\n[3] Getting execution summary:")
    summary = context.get_execution_summary()
    print(f"  Total executions: {summary['total_executions']}")
    print(f"  Successful: {summary['successful']}")
    print(f"  Failed: {summary['failed']}")

    print("\n✓ Test passed")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("PYNF-AGENT TOOLS TEST SUITE")
    print("=" * 70)

    tests = [
        ("Session Context", test_session_context),
        ("List Modules", test_list_modules),
        ("List Submodules", test_list_submodules),
        ("Get Module Info", test_get_module_info),
        ("List Directory", test_list_directory),
    ]

    failed = []

    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed.append(test_name)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {len(tests) - len(failed)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("\nFailed tests:")
        for test_name in failed:
            print(f"  - {test_name}")
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")


if __name__ == "__main__":
    main()
