"""
Audio hardware mocks for PyAudio, ffmpeg, and audio device operations.

This module provides minimal mocks for audio hardware dependencies while
preserving the audio processing logic in the TTS providers. It mocks:
- PyAudio device enumeration and playback
- ffmpeg/ffplay subprocess operations
- Audio file operations (sox, etc.)
- Speaker/microphone availability detection
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock

import pytest


class MockAudioDevice:
    """Mock audio device for PyAudio simulation."""

    def __init__(self, device_id: int, name: str, max_input_channels: int = 0, max_output_channels: int = 2):
        self.device_id = device_id
        self.name = name
        self.max_input_channels = max_input_channels
        self.max_output_channels = max_output_channels
        self.default_sample_rate = 44100.0


class MockPyAudio:
    """Mock PyAudio for testing audio operations."""

    def __init__(self):
        self.devices = [
            MockAudioDevice(0, "Mock Speaker", 0, 2),
            MockAudioDevice(1, "Mock Microphone", 1, 0),
            MockAudioDevice(2, "Mock Headphones", 0, 2),
        ]
        self.streams = []

    def get_device_count(self) -> int:
        """Get number of available audio devices."""
        return len(self.devices)

    def get_device_info_by_index(self, device_index: int) -> Dict[str, Any]:
        """Get device info by index."""
        if 0 <= device_index < len(self.devices):
            device = self.devices[device_index]
            return {
                "index": device.device_id,
                "name": device.name,
                "maxInputChannels": device.max_input_channels,
                "maxOutputChannels": device.max_output_channels,
                "defaultSampleRate": device.default_sample_rate,
            }
        raise ValueError(f"Invalid device index: {device_index}")

    def get_default_output_device_info(self) -> Dict[str, Any]:
        """Get default output device info."""
        return self.get_device_info_by_index(0)

    def get_default_input_device_info(self) -> Dict[str, Any]:
        """Get default input device info."""
        return self.get_device_info_by_index(1)

    def open(self, **kwargs) -> "MockAudioStream":
        """Open an audio stream."""
        stream = MockAudioStream(**kwargs)
        self.streams.append(stream)
        return stream

    def terminate(self) -> None:
        """Terminate PyAudio."""
        for stream in self.streams:
            stream.close()
        self.streams.clear()


class MockAudioStream:
    """Mock audio stream for PyAudio."""

    def __init__(self, **kwargs):
        self.is_open = True
        self.is_active = False
        self.kwargs = kwargs
        self.written_data = []

    def start_stream(self) -> None:
        """Start the audio stream."""
        self.is_active = True

    def stop_stream(self) -> None:
        """Stop the audio stream."""
        self.is_active = False

    def close(self) -> None:
        """Close the audio stream."""
        self.is_open = False
        self.is_active = False

    def write(self, frames: bytes) -> None:
        """Write audio frames to the stream."""
        if not self.is_open:
            raise RuntimeError("Stream is closed")
        self.written_data.append(frames)

    def read(self, num_frames: int) -> bytes:
        """Read audio frames from the stream."""
        if not self.is_open:
            raise RuntimeError("Stream is closed")
        # Return mock audio data
        return b"\x00" * (num_frames * 2)  # 16-bit mono


class MockFFmpegProcess:
    """Mock subprocess for ffmpeg/ffplay operations."""

    def __init__(self, cmd: List[str], **kwargs):
        self.cmd = cmd
        self.kwargs = kwargs
        self.returncode = 0
        self.stdin = Mock()
        self.stdout = Mock()
        self.stderr = Mock()
        self._poll_result = None
        self._terminated = False

        # Mock stdin as a writable stream
        self.stdin.write = Mock()
        self.stdin.flush = Mock()
        self.stdin.close = Mock()

        # Mock stderr output for debugging
        self.stderr.read = Mock(return_value=b"")

    def poll(self) -> Optional[int]:
        """Check if process has terminated."""
        return self._poll_result

    def wait(self, timeout: Optional[float] = None) -> int:
        """Wait for process to complete."""
        if self._terminated:
            raise subprocess.TimeoutExpired(self.cmd, timeout)
        return self.returncode

    def terminate(self) -> None:
        """Terminate the process."""
        self._terminated = True
        self._poll_result = -15  # SIGTERM

    def kill(self) -> None:
        """Kill the process."""
        self._terminated = True
        self._poll_result = -9  # SIGKILL

    def communicate(self, input: Optional[bytes] = None, timeout: Optional[float] = None) -> tuple:
        """Communicate with process."""
        return (b"", b"")


class AudioEnvironmentMock:
    """Mock audio environment detection."""

    def __init__(self, available: bool = True, pulse_available: bool = True, alsa_available: bool = True):
        self.available = available
        self.pulse_available = pulse_available
        self.alsa_available = alsa_available
        self.reason = "Mock audio environment" if available else "Audio disabled for testing"

    def check_audio_environment(self) -> Dict[str, Any]:
        """Mock check_audio_environment function."""
        return {
            "available": self.available,
            "reason": self.reason,
            "pulse_available": self.pulse_available,
            "alsa_available": self.alsa_available,
        }


def mock_subprocess_popen(cmd: List[str], **kwargs) -> MockFFmpegProcess:
    """Mock subprocess.Popen for ffmpeg/ffplay commands."""
    return MockFFmpegProcess(cmd, **kwargs)


def mock_subprocess_run(cmd: List[str], **kwargs) -> MagicMock:
    """Mock subprocess.run for one-off commands."""
    result = MagicMock()
    result.returncode = 0
    result.stdout = b""
    result.stderr = b""
    return result


def mock_shutil_which(cmd: str) -> Optional[str]:
    """Mock shutil.which to simulate available commands."""
    available_commands = {"ffmpeg", "ffplay", "sox"}
    if cmd in available_commands:
        return f"/usr/bin/{cmd}"
    return None


# Pytest fixtures


@pytest.fixture
def mock_pyaudio(monkeypatch):
    """Mock PyAudio for audio device testing."""
    mock_pyaudio_instance = MockPyAudio()

    # Mock PyAudio class
    def mock_pyaudio_class():
        return mock_pyaudio_instance

    monkeypatch.setattr("pyaudio.PyAudio", mock_pyaudio_class, raising=False)

    return mock_pyaudio_instance


@pytest.fixture
def mock_audio_environment(monkeypatch):
    """Mock audio environment detection."""
    env_mock = AudioEnvironmentMock()

    monkeypatch.setattr("tts.audio_utils.check_audio_environment", env_mock.check_audio_environment)

    return env_mock


@pytest.fixture
def mock_audio_environment_unavailable(monkeypatch):
    """Mock audio environment as unavailable."""
    env_mock = AudioEnvironmentMock(available=False)

    monkeypatch.setattr("tts.audio_utils.check_audio_environment", env_mock.check_audio_environment)

    return env_mock


@pytest.fixture
def mock_ffmpeg_operations(monkeypatch):
    """Mock ffmpeg/ffplay subprocess operations."""

    # Track created processes for debugging
    created_processes = []

    def tracking_popen(cmd: List[str], **kwargs) -> MockFFmpegProcess:
        process = mock_subprocess_popen(cmd, **kwargs)
        created_processes.append(process)
        return process

    monkeypatch.setattr("subprocess.Popen", tracking_popen)
    monkeypatch.setattr("subprocess.run", mock_subprocess_run)
    monkeypatch.setattr("shutil.which", mock_shutil_which)

    return {"processes": created_processes}


@pytest.fixture
def mock_ffmpeg_unavailable(monkeypatch):
    """Mock ffmpeg as unavailable."""

    def mock_which_no_ffmpeg(cmd: str) -> Optional[str]:
        return None

    def mock_popen_file_not_found(cmd: List[str], **kwargs) -> MockFFmpegProcess:
        raise FileNotFoundError(f"Command not found: {cmd[0]}")

    monkeypatch.setattr("shutil.which", mock_which_no_ffmpeg)
    monkeypatch.setattr("subprocess.Popen", mock_popen_file_not_found)


@pytest.fixture
def mock_audio_file_operations(monkeypatch, tmp_path):
    """Mock audio file conversion and manipulation."""

    # Track file operations
    conversions = []

    def mock_convert_audio(input_path: str, output_path: str, output_format: str) -> None:
        """Mock audio conversion."""
        conversions.append((input_path, output_path, output_format))

        # Create mock output file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(b"mock_converted_audio_data")

    def mock_stream_audio_file(audio_path: str) -> None:
        """Mock audio streaming."""
        conversions.append(("stream", audio_path, "playback"))

    monkeypatch.setattr("tts.audio_utils.convert_audio", mock_convert_audio)
    monkeypatch.setattr("tts.audio_utils.stream_audio_file", mock_stream_audio_file)

    return {"conversions": conversions}


@pytest.fixture
def mock_tempfile_operations(monkeypatch, tmp_path):
    """Mock temporary file operations."""

    created_files = []

    def mock_named_temporary_file(suffix: str = "", delete: bool = True, **kwargs):
        """Mock NamedTemporaryFile."""
        file_path = tmp_path / f"mock_temp{suffix}"
        created_files.append(str(file_path))

        # Create the file
        file_path.touch()

        # Return a mock file object
        mock_file = Mock()
        mock_file.name = str(file_path)
        mock_file.write = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock()

        return mock_file

    monkeypatch.setattr("tempfile.NamedTemporaryFile", mock_named_temporary_file)

    return {"created_files": created_files}


@pytest.fixture
def comprehensive_audio_mocks(
    mock_pyaudio, mock_audio_environment, mock_ffmpeg_operations, mock_audio_file_operations, mock_tempfile_operations
):
    """Comprehensive audio mocking for full provider testing."""
    return {
        "pyaudio": mock_pyaudio,
        "environment": mock_audio_environment,
        "ffmpeg": mock_ffmpeg_operations,
        "file_ops": mock_audio_file_operations,
        "tempfile": mock_tempfile_operations,
    }


# Utility functions for specific test scenarios


def create_audio_device_busy_scenario(mock_pyaudio: MockPyAudio) -> None:
    """Create a scenario where audio devices are busy."""

    def failing_open(**kwargs):
        raise OSError("Device busy")

    mock_pyaudio.open = failing_open


def create_ffmpeg_broken_pipe_scenario(mock_ffmpeg: Dict[str, Any]) -> None:
    """Create a scenario where ffmpeg encounters broken pipe."""

    def failing_write(data: bytes) -> None:
        raise BrokenPipeError("Broken pipe")

    for process in mock_ffmpeg["processes"]:
        process.stdin.write = failing_write


def create_audio_conversion_failure_scenario(monkeypatch) -> None:
    """Create a scenario where audio conversion fails."""

    def failing_convert_audio(input_path: str, output_path: str, output_format: str) -> None:
        raise RuntimeError("Audio conversion failed")

    monkeypatch.setattr("tts.audio_utils.convert_audio", failing_convert_audio)
