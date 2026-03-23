from unittest.mock import AsyncMock

import pytest

from app.services.validation import ValidationError, validate_upload


def _fake_upload(
    content: bytes = b"\x00" * 1024,
    content_type: str = "video/mp4",
    filename: str = "test.mp4",
) -> AsyncMock:
    """Build a mock UploadFile"""
    mock = AsyncMock()
    mock.filename = filename
    mock.content_type = content_type
    mock.read.return_value = content

    return mock


class TestValidateUpload:
    async def test_valid_file_returns_bytes(self):
        content = b"\x00" * 2048
        file = _fake_upload(content=content)
        result = await validate_upload(file)
        assert result == content

    async def test_reject_unsupported_mime_type(self):
        file = _fake_upload(content_type="image/png")

        with pytest.raises(ValidationError, match="Unsupported file type"):
            await validate_upload(file)

    @pytest.mark.parametrize(
        "mime",
        [
            "video/mp4",
            "video/webm",
            "video/ogg",
            "video/mpeg",
            "video/x-msvideo",
            "video/mp2t",
        ],
    )
    async def test_accepts_all_allowed_mime_types(self, mime):
        file = _fake_upload(content_type=mime)

        result = await validate_upload(file)

        assert isinstance(result, bytes)
