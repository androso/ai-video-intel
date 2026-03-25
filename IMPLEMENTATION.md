# AI Video Intelligence Platform

**Status:** Backlog · **Completion:** 0% · **Priority:** High

Backend-first platform that ingests video, normalizes media, transcribes audio, enriches content with AI, and exposes timeline-based insights through APIs and a demo dashboard.

---

## Concept

A backend-first portfolio project that simulates the core responsibilities of an AI Integration Engineer inside a video product. The system ingests recorded video, normalizes media formats, extracts audio, generates transcripts, enriches the content with AI, and exposes timeline-based insights through APIs and a lightweight dashboard.

---

## Why This Project Matters

- Proves **Python backend** strength with APIs, background jobs, and data pipelines
- Demonstrates **AI integration** rather than just prompt-based UI work
- Shows hands-on **video/media processing** with FFmpeg
- Covers **timestamped metadata** such as transcript segments, highlights, and sentiment windows
- Creates a strong portfolio story for roles involving AI pipelines, integrations, and analytics

---

## Stack

| Layer | Technology |
|---|---|
| API | Python + FastAPI |
| Async processing | Celery or Dramatiq + Redis |
| Media processing | FFmpeg |
| Database | PostgreSQL |
| Object storage | Google Cloud Storage |
| Transcription | Whisper API or Whisper local inference |
| AI enrichment | OpenAI / Gemini / Vertex AI |
| Analytics | BigQuery |
| Frontend demo | Vue or React dashboard |

---

## System Flow

1. User uploads a video file.
2. Backend validates the asset and creates a processing job.
3. FFmpeg normalizes the video into a standard format for downstream processing.
4. Audio is extracted and sent to transcription.
5. Transcript segments are stored with timestamps.
6. AI enrichment generates sentiment, topics, summaries, and highlight candidates.
7. Timeline metadata is exposed through REST endpoints.
8. Dashboard renders transcript, markers, and insights on top of a player.

---

## Core Features

### 1. Video Upload and Asset Intake

The platform should accept common formats such as MP4, MOV, and MKV. On upload, the backend should validate file size, duration, codec metadata, and basic integrity before saving the original file.

**How it should work:**

- Client uploads video through a signed upload flow or direct API endpoint
- Backend creates a `video_asset` record with status `uploaded`
- A `processing_job` record is created immediately with status `queued`
- The API returns a job ID so the frontend can poll or subscribe for progress
- Invalid files should fail early with clear error reasons such as unsupported codec, corrupted file, or size limit exceeded

### 2. Video Normalization and Media Preparation

AI pipelines work better when media is standardized. The platform should convert incoming files into a predictable format such as H.264 video + AAC audio in MP4.

**How it should work:**

- FFmpeg reads the original asset and generates a normalized output
- The system stores both the original file and the normalized file
- The pipeline also generates a thumbnail and optional preview clip
- Technical metadata should be stored: duration, resolution, frame rate, audio channels, codec names
- If transcoding fails, the job should move to `failed` and preserve logs for debugging

### 3. Audio Extraction and Transcription

Once the video is normalized, the system should extract audio for speech-to-text processing.

**How it should work:**

- FFmpeg extracts mono audio in a transcription-friendly format
- Long audio can be chunked into smaller windows for reliability
- A transcription worker calls Whisper or another speech-to-text service
- The result is stored as timestamped transcript segments with `start_time`, `end_time`, `text`, and confidence if available
- Transcript segments should be queryable and easy to map back to the player timeline

### 4. AI Enrichment on Top of Transcript Segments

This is where raw transcript becomes product intelligence. The system should turn transcript windows into structured metadata.

**How it should work:**

- Group transcript segments into short windows such as 20–60 seconds
- Run enrichment jobs for sentiment, topic labels, summaries, and highlight scoring
- Store both raw model output and normalized structured output
- Each insight should reference a time interval, not just a general video-level summary
- Highlight candidates should include a reason such as emotional intensity, topic shift, keyword density, or strong engagement language

### 5. Timeline Intelligence API

The product value comes from turning AI outputs into something the application can consume cleanly.

**How it should work:**

- Provide endpoints for transcript segments, highlights, chapters, sentiment windows, and summaries
- Every response should include time boundaries so the frontend can draw markers on a timeline
- Support filtering by time range, topic, sentiment, and confidence threshold
- Keep the response schema stable so downstream clients can integrate without extra transformations

### 6. Searchable Metadata and Playback Experience

Users should be able to jump directly to meaningful moments instead of manually scrubbing through long videos.

**How it should work:**

- Full-text search over transcript text and extracted topics
- Clicking a search result seeks the player to the exact timestamp
- Highlight cards should jump to the corresponding moment in the video
- Chapters should help users skim the video structure quickly
- The dashboard should visually align transcript, sentiment trend, and highlight markers in one place

### 7. Processing Observability and Failure Recovery

A real integration project must make failures visible.

**How it should work:**

- Each step should have explicit states: `queued`, `processing`, `completed`, `failed`
- The job detail view should show which stage failed
- Store logs, retry counts, and failure reasons for each processing step
- Retrying a failed job should re-run only the failed stage when possible
- Idempotent job design should prevent duplicate metadata when retries happen

### 8. Analytics Pipeline

The platform should not only process a single asset but also generate operational insights.

**How it should work:**

- Push derived metrics to BigQuery or another analytics store
- Track metrics such as processing duration, transcription duration, highlight count, average sentiment, and failure rate
- Support simple reporting like "videos processed this week" or "average processing time by duration bucket"
- Keep product analytics separate from transactional storage in PostgreSQL

---

## Suggested Data Model

- **video_assets**: original file, normalized file, status, duration, technical metadata
- **processing_jobs**: current pipeline stage, retries, error messages, timestamps
- **transcript_segments**: text, start/end time, confidence, speaker (optional)
- **insight_segments**: sentiment, topic, score, highlight reason, model version
- **video_summaries**: short summary, chapter summary, key topics
- **analytics_events**: operational metrics and reporting events

---

## MVP Success Criteria

- Upload a real video and process it end-to-end
- Return transcript segments with correct timestamps
- Generate at least sentiment + topics + highlight suggestions
- Expose a clean API for timeline consumption
- Show all insights working inside a small dashboard demo

---

## Tasks

All tasks are listed below in implementation order. Every task status is **Not started**.

---

### 01. FastAPI foundation, Docker, env config, and CI

| Field | Value |
|---|---|
| **Category** | Backend |
| **Priority** | High |
| **Tags** | Website |

**Summary:** Set up the Python project structure, FastAPI app, environment management, Docker workflow, and CI pipeline.

**Description:** Set up the project so everything else has a stable base. Create the FastAPI app structure, configure environment variables, add Docker for local development, and set up a basic CI workflow to run tests and linting on every push.

---

### 02. Data model for assets, jobs, transcripts, and insights

| Field | Value |
|---|---|
| **Category** | Backend |
| **Priority** | High |
| **Tags** | Website |

**Summary:** Design the PostgreSQL schema for video assets, processing jobs, transcript segments, AI insights, and summary records.

**Description:** Design the core tables before building pipeline logic. Define how videos, processing jobs, transcript segments, insight segments, and summaries relate to each other so the data stays clean and easy to query later.

---

### 03. Video upload flow and object storage integration

| Field | Value |
|---|---|
| **Category** | Backend |
| **Priority** | High |
| **Tags** | Website |

**Summary:** Implement upload endpoints, file validation, and storage of original assets in object storage with job creation.

**Description:** Build the first real user flow: upload a video and store it safely. Add file validation, save the original asset to storage, create the video record in the database, and trigger the first processing job.

---

### 04. FFmpeg normalization, thumbnails, and metadata extraction

| Field | Value |
|---|---|
| **Category** | Backend |
| **Priority** | High |
| **Tags** | Website |

**Summary:** Normalize incoming video formats with FFmpeg, generate thumbnails, and persist media metadata for downstream processing.

**Description:** Prepare all uploaded videos into one predictable format. Use FFmpeg to normalize video/audio, generate thumbnails, and extract technical metadata like duration, resolution, codecs, and frame rate for later pipeline steps.

---

### 05. Audio extraction and transcription pipeline

| Field | Value |
|---|---|
| **Category** | Backend |
| **Priority** | High |
| **Tags** | Website |

**Summary:** Extract audio, run speech-to-text, and store timestamped transcript segments in a queryable format.

**Description:** Turn video audio into structured text. Extract the audio track, send it through speech-to-text, and store timestamped transcript chunks so every line can be matched back to the exact part of the video.

---

### 06. Metadata persistence and job-state tracking

| Field | Value |
|---|---|
| **Category** | Backend |
| **Priority** | High |
| **Tags** | Website |

**Summary:** Persist processing state across stages, track failures and retries, and ensure timeline metadata stays consistent.

**Description:** Make the pipeline reliable and traceable. Track each stage of processing, store success or failure states, save retry information, and make sure the system can recover without duplicating data or losing progress.

---

### 07. AI enrichment for sentiment, topics, summaries, and highlights

| Field | Value |
|---|---|
| **Category** | Backend |
| **Priority** | High |
| **Tags** | Website |

**Summary:** Transform transcript windows into structured AI insights with time ranges and normalized output schemas.

**Description:** Add the AI layer on top of the transcript. Group transcript text into short windows, generate sentiment and topic labels, create summaries, and score highlight candidates so the output becomes useful product metadata.

---

### 08. Timeline intelligence API and transcript search

| Field | Value |
|---|---|
| **Category** | Backend |
| **Priority** | Medium |
| **Tags** | Website |

**Summary:** Expose transcript, highlights, chapters, and search endpoints that the frontend can use without extra transformation.

**Description:** Expose the processed results through clean APIs. Create endpoints for transcript segments, highlights, chapters, and search so a frontend can easily render markers, jump to timestamps, and filter insights.

---

### 09. BigQuery analytics and processing metrics

| Field | Value |
|---|---|
| **Category** | Backend |
| **Priority** | Medium |
| **Tags** | Website |

**Summary:** Push operational and derived metrics into BigQuery to analyze throughput, failures, and asset processing performance.

**Description:** Add reporting for how the system performs over time. Send operational data to BigQuery, track metrics like processing time and failures, and make it possible to analyze how efficient and reliable the pipeline is.

---

### 10. Demo dashboard, deployment, and documentation

| Field | Value |
|---|---|
| **Category** | Backend |
| **Priority** | Medium |
| **Tags** | Website |

**Summary:** Build a simple dashboard to visualize the pipeline results, deploy the system, and document architecture and tradeoffs.

**Description:** Package the project so it is easy to show and explain. Build a small dashboard, deploy the main services, and write documentation that explains the architecture, the flow, and the technical decisions behind the project.

---

### 11. Frontend upload page and project shell

| Field | Value |
|---|---|
| **Category** | Frontend |
| **Priority** | Medium |
| **Tags** | Frontend, Website |

**Summary:** Create the minimal frontend shell with routing and an upload screen that sends videos to the backend.

**Description:** Build the small frontend starting point for the demo. Set up the app shell, routing, and an upload page so users can submit a video and start the processing flow from a simple interface.

---

### 12. Frontend processing status and job progress view

| Field | Value |
|---|---|
| **Category** | Frontend |
| **Priority** | Medium |
| **Tags** | Frontend, Website |

**Summary:** Show upload state, pipeline progress, and failure details using the backend job status endpoints.

**Description:** Create a status screen that shows what stage the pipeline is in after upload. The page should make queued, processing, completed, and failed states easy to understand for a demo viewer.

---

### 13. Frontend video player, transcript panel, and search UI

| Field | Value |
|---|---|
| **Category** | Frontend |
| **Priority** | Medium |
| **Tags** | Frontend, Website |

**Summary:** Build the viewer interface with a player, transcript list, and search box that jumps to exact timestamps.

**Description:** Build the main playback interface for the project demo. Combine the video player, transcript panel, and transcript search so users can explore the processed content and jump directly to important moments.

---

### 14. Frontend highlights, chapters, and timeline visualization

| Field | Value |
|---|---|
| **Category** | Frontend |
| **Priority** | Medium |
| **Tags** | Frontend, Website |

**Summary:** Visualize highlights, chapter markers, and sentiment/timeline insights from the processed metadata.

**Description:** Add the visual layer that makes the AI output feel like a product. Show highlight cards, chapter markers, and timeline indicators so the backend insights are easy to see and demo.

---

## Task Summary

| # | Task | Category | Priority | Status |
|---|---|---|---|---|
| 01 | FastAPI foundation, Docker, env config, and CI | Backend | High | Not started |
| 02 | Data model for assets, jobs, transcripts, and insights | Backend | High | Not started |
| 03 | Video upload flow and object storage integration | Backend | High | Not started |
| 04 | FFmpeg normalization, thumbnails, and metadata extraction | Backend | High | Not started |
| 05 | Audio extraction and transcription pipeline | Backend | High | Not started |
| 06 | Metadata persistence and job-state tracking | Backend | High | Not started |
| 07 | AI enrichment for sentiment, topics, summaries, and highlights | Backend | High | Not started |
| 08 | Timeline intelligence API and transcript search | Backend | Medium | Not started |
| 09 | BigQuery analytics and processing metrics | Backend | Medium | Not started |
| 10 | Demo dashboard, deployment, and documentation | Backend | Medium | Not started |
| 11 | Frontend upload page and project shell | Frontend | Medium | Not started |
| 12 | Frontend processing status and job progress view | Frontend | Medium | Not started |
| 13 | Frontend video player, transcript panel, and search UI | Frontend | Medium | Not started |
| 14 | Frontend highlights, chapters, and timeline visualization | Frontend | Medium | Not started |