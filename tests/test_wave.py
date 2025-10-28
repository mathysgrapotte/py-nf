"""
Unit tests for Wave client.

These tests use mocking to avoid actual API calls to Wave service.
For integration tests, set WAVE_INTEGRATION_TESTS=1 environment variable.
"""

import os
import pytest
from unittest.mock import Mock, patch
from pynf.wave import WaveClient


# Fixtures
@pytest.fixture
def wave_client():
    """Create WaveClient instance for testing."""
    return WaveClient(
        endpoint="https://wave.test", tower_token="test-token", tower_workspace_id=123
    )


@pytest.fixture
def mock_wave_response():
    """Mock successful Wave API response."""
    return {
        "containerImage": "wave.seqera.io/wt/abc123/wave/library:latest",
        "id": "wave-id-123",
        "buildId": "build-id-456",
        "targetImage": "docker.io/user/repo:tag",
    }


@pytest.fixture
def mock_build_status_response():
    """Mock build status API response."""
    return {
        "id": "build-id-456",
        "status": "COMPLETED",
        "succeeded": True,
        "duration": 120.5,
    }


# WaveClient Tests
class TestWaveClient:
    """Tests for WaveClient class."""

    def test_initialization_defaults(self, monkeypatch):
        """Test WaveClient initializes with default values."""
        # Clear environment variables that might be set
        monkeypatch.delenv("TOWER_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("TOWER_WORKSPACE_ID", raising=False)
        monkeypatch.delenv("WAVE_ENDPOINT", raising=False)

        client = WaveClient()
        assert client.endpoint == "https://wave.seqera.io"
        assert client.tower_token is None
        assert client.tower_workspace_id is None

    def test_initialization_with_env_vars(self, monkeypatch):
        """Test WaveClient reads from environment variables."""
        monkeypatch.setenv("WAVE_ENDPOINT", "https://wave.custom")
        monkeypatch.setenv("TOWER_ACCESS_TOKEN", "env-token")
        monkeypatch.setenv("TOWER_WORKSPACE_ID", "999")

        client = WaveClient()
        assert client.endpoint == "https://wave.custom"
        assert client.tower_token == "env-token"
        assert client.tower_workspace_id == 999

    @patch("pynf.wave.requests.Session.post")
    def test_build_from_conda_success(self, mock_post, wave_client, mock_wave_response):
        """Test building container from conda packages."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_wave_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = wave_client.build_from_conda(
            packages=["samtools=1.19", "bcftools"], channels=["conda-forge", "bioconda"]
        )

        assert result["succeeded"] is True
        assert "wave.seqera.io" in result["container_url"]
        assert result["build_id"] == "build-id-456"

        # Verify request payload
        call_args = mock_post.call_args
        request_body = call_args[1]["json"]
        assert request_body["packages"]["type"] == "CONDA"
        assert "samtools=1.19" in request_body["packages"]["entries"]
        assert "conda-forge" in request_body["packages"]["conda_opts"]["channels"]

    @patch("pynf.wave.requests.Session.post")
    def test_build_from_dockerfile_success(
        self, mock_post, wave_client, mock_wave_response
    ):
        """Test building container from Dockerfile."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_wave_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        dockerfile = "FROM ubuntu:22.04\nRUN apt-get update"
        result = wave_client.build_from_dockerfile(
            dockerfile_content=dockerfile, build_repository="docker.io/test/repo"
        )

        assert result["succeeded"] is True
        assert result["target_image"] == "docker.io/user/repo:tag"

        # Verify Dockerfile in request
        call_args = mock_post.call_args
        request_body = call_args[1]["json"]
        assert request_body["containerFile"] == dockerfile
        assert request_body["buildRepository"] == "docker.io/test/repo"

    def test_build_from_dockerfile_requires_repository(self, wave_client):
        """Test that Dockerfile builds require build_repository."""
        with pytest.raises(ValueError, match="build_repository is required"):
            wave_client.build_from_dockerfile(
                dockerfile_content="FROM ubuntu:22.04", build_repository=None
            )

    @patch("pynf.wave.requests.Session.post")
    def test_augment_container_success(
        self, mock_post, wave_client, mock_wave_response
    ):
        """Test augmenting existing container."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_wave_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = wave_client.augment_container(
            base_image="ubuntu:22.04", conda_packages=["samtools", "bcftools"]
        )

        assert result["succeeded"] is True

        # Verify request includes packages
        call_args = mock_post.call_args
        request_body = call_args[1]["json"]
        assert request_body["containerImage"] == "ubuntu:22.04"
        assert "samtools" in request_body["packages"]["entries"]

    @patch("pynf.wave.requests.Session.get")
    def test_check_build_status_completed(
        self, mock_get, wave_client, mock_build_status_response
    ):
        """Test checking build status when build is complete."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_build_status_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = wave_client.check_build_status(
            build_id="build-id-456", timeout=10, poll_interval=1
        )

        assert result["status"] == "COMPLETED"
        assert result["succeeded"] is True
        assert result["duration"] == 120.5

    @patch("pynf.wave.requests.Session.get")
    @patch("pynf.wave.time.sleep")  # Mock sleep to speed up test
    def test_check_build_status_timeout(self, mock_sleep, mock_get, wave_client):
        """Test build status check timeout."""
        # Simulate pending status that never completes
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "PENDING", "id": "build-123"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = wave_client.check_build_status(
            build_id="build-123",
            timeout=5,  # Short timeout
            poll_interval=1,
        )

        assert result["status"] == "TIMEOUT"
        assert result["succeeded"] is False

    @patch("pynf.wave.requests.Session.post")
    def test_api_error_handling(self, mock_post, wave_client):
        """Test handling of API errors."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid request"}
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = Exception("HTTP 400")
        mock_post.return_value = mock_response

        result = wave_client.build_from_conda(packages=["invalid"])

        assert result["succeeded"] is False
        assert "error" in result


# Integration Tests (run only when WAVE_INTEGRATION_TESTS=1)
@pytest.mark.skipif(
    os.getenv("WAVE_INTEGRATION_TESTS") != "1",
    reason="Integration tests disabled. Set WAVE_INTEGRATION_TESTS=1 to enable",
)
class TestWaveIntegration:
    """Integration tests that make real API calls to Wave service."""

    def test_real_conda_build(self):
        """Test real container build from conda packages."""
        client = WaveClient()
        result = client.build_from_conda(packages=["cowsay"], channels=["conda-forge"])

        assert result["succeeded"] is True
        assert result["container_url"] is not None
        print(f"Built container: {result['container_url']}")

    def test_real_augment(self):
        """Test real container augmentation."""
        client = WaveClient()
        result = client.augment_container(
            base_image="ubuntu:22.04", conda_packages=["cowsay"]
        )

        assert result["succeeded"] is True
        assert result["container_url"] is not None
        print(f"Augmented container: {result['container_url']}")
