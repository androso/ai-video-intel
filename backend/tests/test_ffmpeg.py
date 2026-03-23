import json
import subprocess
from unittest.mock import patch

import pytest

from app.services.ffmpeg import (
    FFmpegError,
    MediaInfo,
    generate_thumbnail,
    probe_media,
    transcode_to_standard,
)

PROBE_JSON_H264_AAC: dict = {
    "streams": [
        {
            "codec_type": "video",
            "codec_name": "h264",
            "width": 1920,
            "height": 1080,
            "r_frame_rate": "30000/1001",
            "avg_frame_rate": "30000/1001",
            "duration": "120.500",
        },
        {
            "codec_type": "audio",
            "codec_name": "aac",
            "channels": 2,
            "sample_rate": "44100",
        },
    ],
    "format": {
        "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        "duration": "120.500",
        "bit_rate": "5000000",
    },
}

PROBE_JSON_VP9_OPUS: dict = {
    "streams": [
        {
            "codec_type": "video",
            "codec_name": "vp9",
            "width": 1280,
            "height": 720,
            "r_frame_rate": "25/1",
            "avg_frame_rate": "25/1",
        },
        {
            "codec_type": "audio",
            "codec_name": "opus",
            "channels": 1,
            "sample_rate": "48000",
        },
    ],
    "format": {
        "format_name": "matroska,webm",
        "duration": "60.000",
        "bit_rate": "2500000",
    },
}

PROBE_JSON_NO_AUDIO: dict = {
    "streams": [
        {
            "codec_type": "video",
            "codec_name": "h264",
            "width": 640,
            "height": 480,
            "r_frame_rate": "24/1",
            "avg_frame_rate": "24/1",
        },
    ],
    "format": {
        "format_name": "mp4",
        "duration": "10.000",
    },
}


def _mock_run_ok(
    stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=[], returncode=0, stdout=stdout, stderr=stderr
    )


def _mock_run_fail(stderr: str = "error") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr=stderr)


class TestProbeMedia:
    @patch("app.services.ffmpeg._run")
    def test_parses_h264_aac_mp4(self, mock_run):
        mock_run.return_value = _mock_run_ok(stdout=json.dumps(PROBE_JSON_H264_AAC))

        info = probe_media("/tmp/test.mp4")

        assert info.duration_seconds == 120.5
        assert info.width == 1920
        assert info.height == 1080
        assert info.fps == pytest.approx(29.97, abs=0.01)
        assert info.video_codec == "h264"
        assert info.audio_codec == "aac"
        assert info.audio_channels == 2
        assert info.audio_sample_rate == 44100
        assert "mp4" in info.file_format
        assert info.bitrate == 5_000_000

    @patch("app.services.ffmpeg._run")
    def test_parses_vp9_opus_webm(self, mock_run):
        mock_run.return_value = _mock_run_ok(stdout=json.dumps(PROBE_JSON_VP9_OPUS))

        info = probe_media("/tmp/test.webm")

        assert info.video_codec == "vp9"
        assert info.audio_codec == "opus"
        assert info.width == 1280
        assert info.height == 720
        assert info.fps == 25.0
        assert info.duration_seconds == 60.0

    @patch("app.services.ffmpeg._run")
    def test_handles_no_audio_stream(self, mock_run):
        mock_run.return_value = _mock_run_ok(stdout=json.dumps(PROBE_JSON_NO_AUDIO))

        info = probe_media("/tmp/silent.mp4")

        assert info.audio_codec is None
        assert info.audio_channels is None
        assert info.audio_sample_rate is None

    @patch("app.services.ffmpeg._run")
    def test_raises_on_no_video_stream(self, mock_run):
        audio_only = {
            "streams": [{"codec_type": "audio", "codec_name": "aac", "channels": 2}],
            "format": {"format_name": "mp3", "duration": "180.0"},
        }
        mock_run.return_value = _mock_run_ok(stdout=json.dumps(audio_only))

        with pytest.raises(FFmpegError, match="No video stream"):
            probe_media("/tmp/audio.mp3")

    @patch("app.services.ffmpeg._run")
    def test_raises_on_invalid_json(self, mock_run):
        mock_run.return_value = _mock_run_ok(stdout="NOT JSON")

        with pytest.raises(FFmpegError, match="Could not parse"):
            probe_media("/tmp/corrupt.mp4")

    @patch("app.services.ffmpeg._run")
    def test_raises_on_ffprobe_failure(self, mock_run):
        mock_run.side_effect = FFmpegError("Command failed", stderr="boom")

        with pytest.raises(FFmpegError):
            probe_media("/tmp/bad.mp4")

    @patch("app.services.ffmpeg._run")
    def test_correct_ffprobe_args(self, mock_run):
        mock_run.return_value = _mock_run_ok(stdout=json.dumps(PROBE_JSON_H264_AAC))

        probe_media("/tmp/test.mp4")

        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffprobe"
        assert "-v" in cmd and "quiet" in cmd
        assert "-print_format" in cmd and "json" in cmd
        assert "-show_format" in cmd
        assert "-show_streams" in cmd
        assert cmd[-1] == "/tmp/test.mp4"


class TestIsAlreadyNormalized:
    def test_h264_aac_mp4_is_normalized(self):
        info = MediaInfo(
            duration_seconds=60,
            width=1920,
            height=1080,
            fps=30,
            video_codec="h264",
            audio_codec="aac",
            audio_channels=2,
            audio_sample_rate=44100,
            file_format="mov,mp4,m4a,3gp,3g2,mj2",
            bitrate=5000000,
        )
        assert info.is_already_normalized is True

    def test_vp9_opus_webm_not_normalized(self):
        info = MediaInfo(
            duration_seconds=60,
            width=1280,
            height=720,
            fps=25,
            video_codec="vp9",
            audio_codec="opus",
            audio_channels=1,
            audio_sample_rate=48000,
            file_format="matroska,webm",
            bitrate=2500000,
        )
        assert info.is_already_normalized is False

    def test_h264_no_audio_mp4_is_normalized(self):
        info = MediaInfo(
            duration_seconds=10,
            width=640,
            height=480,
            fps=24,
            video_codec="h264",
            audio_codec=None,
            audio_channels=None,
            audio_sample_rate=None,
            file_format="mp4",
            bitrate=None,
        )
        assert info.is_already_normalized is True

    def test_h264_mp3_in_mp4_not_normalized(self):
        info = MediaInfo(
            duration_seconds=30,
            width=1920,
            height=1080,
            fps=30,
            video_codec="h264",
            audio_codec="mp3",
            audio_channels=2,
            audio_sample_rate=44100,
            file_format="mp4",
            bitrate=4000000,
        )
        assert info.is_already_normalized is False


class TestMediaInfoToDict:
    def test_round_trips_all_fields(self):
        info = MediaInfo(
            duration_seconds=120.5,
            width=1920,
            height=1080,
            fps=29.97,
            video_codec="h264",
            audio_codec="aac",
            audio_channels=2,
            audio_sample_rate=44100,
            file_format="mp4",
            bitrate=5000000,
        )
        d = info.to_dict()
        assert d["duration_seconds"] == 120.5
        assert d["width"] == 1920
        assert d["video_codec"] == "h264"
        assert d["bitrate"] == 5000000
        assert len(d) == 10


class TestTranscodeToStandard:
    @patch("app.services.ffmpeg._run")
    def test_copy_mode_when_already_normalized(self, mock_run, tmp_path):
        info = MediaInfo(
            duration_seconds=60,
            width=1920,
            height=1080,
            fps=30,
            video_codec="h264",
            audio_codec="aac",
            audio_channels=2,
            audio_sample_rate=44100,
            file_format="mov,mp4,m4a,3gp,3g2,mj2",
            bitrate=5000000,
        )
        out = str(tmp_path / "out.mp4")

        transcode_to_standard("/tmp/input.mp4", out, info)

        cmd = mock_run.call_args[0][0]
        assert "-c" in cmd and "copy" in cmd
        assert "-movflags" in cmd
        assert "libx264" not in cmd

    @patch("app.services.ffmpeg._run")
    def test_full_transcode_when_not_normalized(self, mock_run, tmp_path):
        info = MediaInfo(
            duration_seconds=60,
            width=1280,
            height=720,
            fps=25,
            video_codec="vp9",
            audio_codec="opus",
            audio_channels=1,
            audio_sample_rate=48000,
            file_format="matroska,webm",
            bitrate=2500000,
        )
        out = str(tmp_path / "out.mp4")

        transcode_to_standard("/tmp/input.webm", out, info)

        cmd = mock_run.call_args[0][0]
        assert "libx264" in cmd
        assert "aac" in cmd
        assert "-crf" in cmd
        assert "-movflags" in cmd and "+faststart" in cmd

    @patch("app.services.ffmpeg._run")
    def test_creates_output_directory(self, mock_run, tmp_path):
        info = MediaInfo(
            duration_seconds=10,
            width=640,
            height=480,
            fps=24,
            video_codec="vp9",
            audio_codec="opus",
            audio_channels=2,
            audio_sample_rate=48000,
            file_format="webm",
            bitrate=1000000,
        )
        nested = tmp_path / "deep" / "nested"
        out = str(nested / "out.mp4")

        transcode_to_standard("/tmp/in.webm", out, info)

        assert nested.exists()

    @patch("app.services.ffmpeg._run")
    def test_raises_on_ffmpeg_failure(self, mock_run, tmp_path):
        mock_run.side_effect = FFmpegError("Command failed", stderr="encoding error")
        info = MediaInfo(
            duration_seconds=10,
            width=640,
            height=480,
            fps=24,
            video_codec="vp9",
            audio_codec="opus",
            audio_channels=2,
            audio_sample_rate=48000,
            file_format="webm",
            bitrate=1000000,
        )

        with pytest.raises(FFmpegError):
            transcode_to_standard("/tmp/in.webm", str(tmp_path / "out.mp4"), info)


class TestGenerateThumbnail:
    @patch("app.services.ffmpeg._run")
    def test_correct_args_with_timestamp(self, mock_run, tmp_path):
        out = str(tmp_path / "thumb.jpg")

        generate_thumbnail("/tmp/video.mp4", out, timestamp=30.5)

        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "-ss" in cmd
        ss_idx = cmd.index("-ss")
        assert cmd[ss_idx + 1] == "30.500"
        assert "-vframes" in cmd and "1" in cmd
        assert cmd[-1] == out

    @patch("app.services.ffmpeg._run")
    def test_default_timestamp_is_zero(self, mock_run, tmp_path):
        out = str(tmp_path / "thumb.jpg")

        generate_thumbnail("/tmp/video.mp4", out)

        cmd = mock_run.call_args[0][0]
        ss_idx = cmd.index("-ss")
        assert cmd[ss_idx + 1] == "0.000"

    @patch("app.services.ffmpeg._run")
    def test_creates_output_directory(self, mock_run, tmp_path):
        nested = tmp_path / "thumbs" / "sub"
        out = str(nested / "thumb.jpg")

        generate_thumbnail("/tmp/video.mp4", out)

        assert nested.exists()

    @patch("app.services.ffmpeg._run")
    def test_raises_on_failure(self, mock_run, tmp_path):
        mock_run.side_effect = FFmpegError("Command failed")

        with pytest.raises(FFmpegError):
            generate_thumbnail("/tmp/bad.mp4", str(tmp_path / "t.jpg"))


class TestRunTimeout:
    @patch("subprocess.run")
    def test_timeout_raises_ffmpeg_error(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            cmd="ffprobe", timeout=600
        )

        with pytest.raises(FFmpegError, match="timed out"):
            probe_media("/tmp/huge.mp4")
