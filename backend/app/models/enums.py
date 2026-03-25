import enum


class AssetStatus(enum.StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class JobStatus(enum.StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepName(enum.StrEnum):
    NORMALIZATION = "normalization"
    AUDIO_EXTRACTION = "audio_extraction"
    TRANSCRIPTION = "transcription"
    AI_ENRICHMENT = "ai_enrichment"


class InsightType(enum.StrEnum):
    SENTIMENT = "sentiment"
    TOPIC = "topic"
    HIGHLIGHT = "highlight"
    CHAPTER = "chapter"