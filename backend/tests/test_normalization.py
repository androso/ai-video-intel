import uuid
from unittest.mock import MagicMock, call, patch

import pytest

from app.services.ffmpeg import MediaInfo
from app.services.normalization import execute_normalization

ASSET_ID = uuid.uuid4()

MEDIA_INFO = MediaInfo(
    duration_seconds=120.0,
    width=1920,
    height=1080,
    fps=30.0,
    video_codec="h264",
    audio_codec="aac",
    audio_channels=2,
    audio_sample_rate=44100,
    file_format="mov,mp4,m4a,3gp,3g2,mj2",
    bitrate=5_000_000,
)


def _make_asset(storage_path: str = "storage/originals/test.mp4") -> MagicMock:
    asset = MagicMock()
    asset.id = ASSET_ID
    asset.original_storage_path = storage_path
    return asset


def _make_job() -> MagicMock:
    job = MagicMock()
    job.id = uuid.uuid4()
    return job


@pytest.fixture()
def mock_ffmpeg_calls():
    """Patch all FFmpeg functions to no-ops returning MEDIA_INFO."""
    with (
        patch("app.services.normalization.probe_media", return_value=MEDIA_INFO) as mock_probe,
        patch("app.services.normalization.transcode_to_standard") as mock_transcode,
        patch("app.services.normalization.generate_thumbnail") as mock_thumb,
    ):
        yield mock_probe, mock_transcode, mock_thumb


@pytest.fixture()
def mock_storage():
    """Patch download_file and store_file."""
    with (
        patch("app.services.normalization.download_file", return_value="storage/originals/test.mp4") as mock_dl,
        patch("app.services.normalization.store_file", side_effect=["normalized/out.mp4", "thumbnails/thumb.jpg"]) as mock_store,
    ):
        yield mock_dl, mock_store


class TestExecuteNormalizationFlow:
    def test_calls_probe_on_downloaded_input(self, mock_ffmpeg_calls, mock_storage, tmp_path):
        mock_probe, mock_transcode, mock_thumb = mock_ffmpeg_calls
        mock_dl, _ = mock_storage
        mock_dl.return_value = "storage/originals/test.mp4"

        asset = _make_asset()
        db = MagicMock()

        with patch("app.services.normalization.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"bytes"))), __exit__=MagicMock(return_value=False)))):
            execute_normalization(db, asset, _make_job())

        mock_probe.assert_called()
        first_probe_path = mock_probe.call_args_list[0][0][0]
        assert first_probe_path == "storage/originals/test.mp4"

    def test_calls_transcode_with_source_media_info(self, mock_ffmpeg_calls, mock_storage):
        mock_probe, mock_transcode, mock_thumb = mock_ffmpeg_calls

        asset = _make_asset()
        db = MagicMock()

        with patch("app.services.normalization.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"bytes"))), __exit__=MagicMock(return_value=False)))):
            execute_normalization(db, asset, _make_job())

        mock_transcode.assert_called_once()
        _, _, passed_info = mock_transcode.call_args[0]
        assert passed_info == MEDIA_INFO

    def test_thumbnail_timestamp_is_25_percent(self, mock_ffmpeg_calls, mock_storage):
        mock_probe, mock_transcode, mock_thumb = mock_ffmpeg_calls

        asset = _make_asset()
        db = MagicMock()

        with patch("app.services.normalization.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"bytes"))), __exit__=MagicMock(return_value=False)))):
            execute_normalization(db, asset, _make_job())

        mock_thumb.assert_called_once()
        ts = mock_thumb.call_args[1]["timestamp"]
        assert ts == pytest.approx(120.0 * 0.25)

    def test_thumbnail_timestamp_is_zero_for_short_video(self, mock_storage):
        short_info = MediaInfo(
            duration_seconds=0.5,
            width=640, height=480, fps=30, video_codec="h264",
            audio_codec="aac", audio_channels=2, audio_sample_rate=44100,
            file_format="mp4", bitrate=1_000_000,
        )
        with (
            patch("app.services.normalization.probe_media", return_value=short_info),
            patch("app.services.normalization.transcode_to_standard"),
            patch("app.services.normalization.generate_thumbnail") as mock_thumb,
            patch("app.services.normalization.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"bytes"))), __exit__=MagicMock(return_value=False)))),
        ):
            execute_normalization(MagicMock(), _make_asset(), _make_job())

        ts = mock_thumb.call_args[1]["timestamp"]
        assert ts == 0.0

    def test_stores_normalized_with_correct_prefix(self, mock_ffmpeg_calls, mock_storage):
        _, mock_store = mock_storage

        with patch("app.services.normalization.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"bytes"))), __exit__=MagicMock(return_value=False)))):
            execute_normalization(MagicMock(), _make_asset(), _make_job())

        prefixes = [c.kwargs.get("prefix") or c[2] for c in mock_store.call_args_list]
        assert "normalized" in prefixes
        assert "thumbnails" in prefixes

    def test_updates_asset_record(self, mock_ffmpeg_calls, mock_storage):
        asset = _make_asset()
        db = MagicMock()

        with patch("app.services.normalization.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"bytes"))), __exit__=MagicMock(return_value=False)))):
            execute_normalization(db, asset, _make_job())

        assert asset.normalized_storage_path is not None
        assert asset.thumbnail_path is not None
        assert asset.duration_seconds == MEDIA_INFO.duration_seconds
        assert asset.technical_metadata == MEDIA_INFO.to_dict()
        db.commit.assert_called()

    def test_cleanup_on_success(self, mock_ffmpeg_calls, mock_storage):
        """Temp directory should be removed even on success."""
        created_dirs = []

        original_mkdtemp = __import__("tempfile").mkdtemp

        def track_mkdtemp(**kwargs):
            path = original_mkdtemp(**kwargs)
            created_dirs.append(path)
            return path

        with (
            patch("app.services.normalization.tempfile.mkdtemp", side_effect=track_mkdtemp),
            patch("app.services.normalization.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"bytes"))), __exit__=MagicMock(return_value=False)))),
        ):
            execute_normalization(MagicMock(), _make_asset(), _make_job())

        import os
        for d in created_dirs:
            assert not os.path.exists(d), f"Temp dir not cleaned up: {d}"


class TestExecuteNormalizationCleanupOnFailure:
    def test_temp_dir_removed_when_probe_fails(self, mock_storage):
        created_dirs = []
        original_mkdtemp = __import__("tempfile").mkdtemp

        def track_mkdtemp(**kwargs):
            path = original_mkdtemp(**kwargs)
            created_dirs.append(path)
            return path

        with (
            patch("app.services.normalization.tempfile.mkdtemp", side_effect=track_mkdtemp),
            patch("app.services.normalization.probe_media", side_effect=RuntimeError("probe failed")),
        ):
            with pytest.raises(RuntimeError, match="probe failed"):
                execute_normalization(MagicMock(), _make_asset(), _make_job())

        import os
        for d in created_dirs:
            assert not os.path.exists(d), f"Temp dir not cleaned up after failure: {d}"

    def test_exception_propagates_from_transcode(self, mock_storage):
        with (
            patch("app.services.normalization.probe_media", return_value=MEDIA_INFO),
            patch("app.services.normalization.transcode_to_standard", side_effect=RuntimeError("transcode failed")),
        ):
            with pytest.raises(RuntimeError, match="transcode failed"):
                execute_normalization(MagicMock(), _make_asset(), _make_job())
