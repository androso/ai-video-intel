import logging
from dataclasses import dataclass
import subprocess
import json
from pathlib import Path

logger = logging.getLogger(__name__)
from app.core.config import settings


class FFmpegError(Exception):
    """raised when an FFmpeg/FFprobe command fails."""

    def __init__(self, message: str, stderr: str = "") -> None:
        self.stderr = stderr
        super().__init__(message)


@dataclass(frozen=True)
class MediaInfo:
    """Structured output from ffprobe"""

    duration_seconds: float
    width: int
    height: int
    fps: float
    video_codec: str
    audio_codec: str | None
    audio_channels: int | None
    audio_sample_rate: int | None
    file_format: str
    bitrate: int | None

    def to_dict(self) -> dict:
        """Serialize to a JSONB for storage purposes"""
        return {
            "duration_seconds": self.duration_seconds,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
            "audio_channels": self.audio_channels,
            "audio_sample_rate": self.audio_sample_rate,
            "file_format": self.file_format,
            "bitrate": self.bitrate,
        }

    @property
    def is_already_normalized(self) -> bool:
        """Return true if the file is already H.264 + AAC in an mp4 container"""
        video_ok = self.video_codec in ("h264", "libx264")
        audio_ok = self.audio_codec in ("aac", None)
        container_ok = "mp4" in self.file_format.lower()
        return video_ok and audio_ok and container_ok


def _run(
    cmd: list[str], timeout: int | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess, returning the result or raising a FFmpegError"""
    effective_timeout = timeout or settings.FFMPEG_TIMEOUT_SECONDS
    logger.debug("Running: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=effective_timeout, check=False
        )
    except subprocess.TimeoutExpired as exc:
        raise FFmpegError(
            f"Command timed out after {effective_timeout}s: {' '.join(cmd)}"
        ) from exc

    if result.returncode != 0:
        raise FFmpegError(
            f"Command failed (exit {result.returncode}): {' '.join(cmd)}",
            stderr=result.stderr,
        )
    return result


def _find_stream(streams: list[dict], codec_type: str) -> dict | None:
    """Return the first stream matching *codec_type* or None"""
    return next((s for s in streams if s.get("codec_type") == codec_type), None)


def _parse_fps(video_stream: dict) -> float:
    """Extract FPS from r_frame_rate or avg_frame_rate as a float"""
    for key in ("r_frame_rate", "avg_frame_rate"):
        raw = video_stream.get(key, "")
        if "/" in raw:
            num, den = raw.split("/", 1)
            try:
                num_f, den_f = float(num), float(den)
                if den_f > 0:
                    return round(num_f / den_f, 3)
            except ValueError:
                continue
    return 0.0


def probe_media(input_path: str) -> MediaInfo:
    """Run ffprobe and return structured media metadata.

    Raises FFmpegError if the file cannot be probed or has no video stream
    """
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        input_path
    ]
    result = _run(cmd)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise FFmpegError(f"Could not parse ffprobe output for {input_path}") from exc

    streams: list[dict] = data.get("streams", {})
    fmt: dict = data.get("format", {})

    video = _find_stream(streams, "video")
    if video is None:
        raise FFmpegError(f"No video stream found in {input_path}")

    audio = _find_stream(streams, "audio")

    duration_raw = fmt.get("duration") or video.get("duration") or "0"
    bitrate_raw = fmt.get("bit_rate")

    return MediaInfo(
        duration_seconds=round(float(duration_raw), 3),
        width=int(video.get("width", 0)),
        height=int(video.get("height", 0)),
        fps=_parse_fps(video),
        video_codec=video.get("codec_name", "unknown"),
        audio_codec=audio.get("codec_name") if audio else None,
        audio_channels=(
            int(audio["channels"]) if audio and "channels" in audio else None
        ),
        audio_sample_rate=(
            int(audio["sample_rate"]) if audio and "sample_rate" in audio else None
        ),
        file_format=fmt.get("format_name", "unknown"),
        bitrate=int(bitrate_raw) if bitrate_raw else None,
    )


def transcode_to_standard(
    input_path: str, output_path: str, media_info: MediaInfo
) -> None:
    """
    Normalize a video file to H.264 + AAC in an mp4 container.

    if the source is already in the target format, streams are copied instead of
    being re-encoded to save time.

    Raises FFmpegError on failure
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if media_info.is_already_normalized:
        logger.info("Input already normalized, copying streams for %s", input_path)
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            output_path,
        ]
    else:
        logger.info("Transcoding %s -> H.264/AAC MP4", input_path)
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-c:v",
            "libx264",
            "-preset",
            settings.NORMALIZED_VIDEO_PRESET,
            "-crf",
            str(settings.NORMALIZED_VIDEO_CRF),
            "-c:a",
            "aac",
            "-b:a",
            settings.NORMALIZED_AUDIO_BITRATE,
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            output_path,
        ]

    _run(cmd)
    logger.info("Transcode complete -> %s", input_path)


def generate_thumbnail(
    input_path: str, output_path: str, timestamp: float = 0.0
) -> None:
    """Extract a single JPEG frame from *input_path* at *timestamp* seconds.

    Raises FFmpegError on failure.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{timestamp:.3f}",
        "-i",
        input_path,
        "-vframes",
        "1",
        "-q:v",
        str(settings.THUMBNAIL_QUALITY),
        output_path,
    ]

    _run(cmd)
    logger.info("Thumbnail generated %s", output_path)
