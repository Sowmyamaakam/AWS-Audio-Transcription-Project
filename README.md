# AWS Audio Transcription Studio

<p align="center">
  <img src="https://img.shields.io/badge/AWS-Lambda-FF9900?style=for-the-badge&logo=awslambda&logoColor=white"/>
  <img src="https://img.shields.io/badge/AWS-Transcribe-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white"/>
  <img src="https://img.shields.io/badge/AWS-S3-569A31?style=for-the-badge&logo=amazons3&logoColor=white"/>
  <img src="https://img.shields.io/badge/AWS-API_Gateway-A100FF?style=for-the-badge&logo=amazon-aws&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python-boto3-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
</p>

<p align="center">
  <b>Upload audio files or record live — get speaker-separated transcripts in seconds.<br/>
  Serverless · Speaker Diarization · Real-time Waveform · 6 Audio Formats</b>
</p>

---

## What It Does

A fully serverless audio transcription pipeline built on AWS. The browser-based frontend lets users either upload existing audio files or record live audio directly, then delivers speaker-labeled transcripts with timestamps — powered entirely by AWS Transcribe's AI speech recognition engine.

- **Upload or Record** — drop a file or record live from the browser microphone
- **Speaker Diarization** — up to 10 speakers identified and labeled with timestamps
- **6 Audio Formats** — MP3, WAV, M4A, MP4, FLAC, OGG
- **Real-time Waveform** — live audio visualizer via Web Audio API + Canvas during recording
- **Async Progress Tracking** — real-time status polling with animated progress bar
- **Local Analysis Tool** — `parse_transcription.py` for detailed confidence score analysis on raw JSON output

---

## Architecture

```
┌─────────────────────────────────┐
│        Browser Frontend          │
│  Upload File  |  Record Live     │
│  (HTML5 + Vanilla JS)            │
└──────────────┬──────────────────┘
               │ HTTPS / JSON
               ▼
┌─────────────────────────────────┐
│       Amazon API Gateway         │
│  POST /upload                    │
│  GET  /status?jobName=...        │
│  GET  /result?jobName=...        │
└──────────────┬──────────────────┘
               │ Invokes
               ▼
┌─────────────────────────────────┐
│        AWS Lambda (Python)       │
│  lambda_function.py              │
│  boto3 · base64 decode           │
│  Unique job naming (uuid)        │
└────────┬─────────────┬──────────┘
         │             │
         ▼             ▼
┌──────────────┐ ┌──────────────────────┐
│  S3 Input    │ │   Amazon Transcribe   │
│  Bucket      │ │                      │
│ (audio files)│ │  Speaker Labels ON   │
└──────────────┘ │  MaxSpeakerLabels=10 │
                 │  LanguageCode=en-US  │
                 └──────────┬───────────┘
                            │ Writes output
                            ▼
                 ┌──────────────────────┐
                 │   S3 Output Bucket   │
                 │  {jobName}.json      │
                 │  (Transcribe result) │
                 └──────────────────────┘
```

---

## Key Features

### Live Browser Recording
The frontend uses the **MediaRecorder API** to capture microphone audio (WebM format) directly in the browser. A real-time waveform visualizer draws frequency bars using the **Web Audio API** + Canvas during recording.

### Speaker Diarization
AWS Transcribe's speaker diarization identifies up to **10 distinct speakers** and assigns labeled segments (`spk_0`, `spk_1`, …) with start/end timestamps. The frontend renders each speaker's lines in separate styled blocks.

### Serverless Pipeline
Zero infrastructure to manage — API Gateway + Lambda handle all traffic. Lambda decodes the base64 audio payload, uploads to S3, and starts an AWS Transcribe job. Results are read from S3 when the job completes.

### Confidence Analysis (Local Tool)
`parse_transcription.py` processes raw Transcribe JSON output locally and reports:
- Average, highest, and lowest word-level confidence scores
- Full transcript and speaker-separated view with timestamps
- Total word count per job

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3 (animations, backdrop-filter), Vanilla JavaScript |
| **Recording** | MediaRecorder API (WebM), Web Audio API, Canvas API |
| **Backend** | Python 3.x, AWS Lambda, boto3 |
| **API Layer** | Amazon API Gateway (REST) |
| **Speech-to-Text** | Amazon Transcribe (speaker diarization enabled) |
| **Storage** | Amazon S3 (2 buckets: input audio + output JSON) |
| **Auth** | AWS IAM (Lambda execution role) |
| **Local Tool** | Python `parse_transcription.py` (confidence analysis) |

---

## Project Structure

```
AWS-Audio-Transcription-Project/
├── index.html                  # Browser frontend — upload + live record + results UI
├── parse_transcription.py      # Local CLI tool — analyze Transcribe JSON output
└── lambda_code/
    └── lambda_function.py      # AWS Lambda handler — 3 API endpoints
```

---

## API Reference

All endpoints are served through Amazon API Gateway at:
```
https://<api-id>.execute-api.us-east-1.amazonaws.com/prod
```

### `POST /upload`

Accepts base64-encoded audio, uploads to S3, and starts an AWS Transcribe job.

**Request:**
```json
{
  "audioData": "data:audio/mp3;base64,//uQxAAAAAAAAAAAAAAAAAAAAAAAW...",
  "filename": "meeting.mp3"
}
```

**Response:**
```json
{
  "message": "Upload successful",
  "jobName": "web-transcribe-20240618-153042-a3f8c1d2",
  "s3Key": "20240618-153042-a3f8c1d2.mp3"
}
```

---

### `GET /status?jobName=<name>`

Polls the AWS Transcribe job status.

**Response (in progress):**
```json
{ "status": "IN_PROGRESS", "jobName": "web-transcribe-..." }
```

**Response (completed):**
```json
{
  "status": "COMPLETED",
  "jobName": "web-transcribe-...",
  "outputUri": "https://s3.amazonaws.com/..."
}
```

---

### `GET /result?jobName=<name>`

Fetches the completed transcript from S3 and returns the full text plus speaker-separated segments.

**Response:**
```json
{
  "transcript": "Hello everyone welcome to the meeting. Let us get started.",
  "jobName": "web-transcribe-...",
  "speakers": [
    {
      "speaker": "spk_0",
      "startTime": "0.0",
      "endTime": "3.45",
      "text": "Hello everyone welcome to the meeting."
    },
    {
      "speaker": "spk_1",
      "startTime": "4.1",
      "endTime": "6.8",
      "text": "Let us get started."
    }
  ]
}
```

---

## AWS Setup

### 1. S3 Buckets

Create two S3 buckets (names must be globally unique):

```bash
aws s3 mb s3://audio-input-yourname-12345 --region us-east-1
aws s3 mb s3://audio-output-yourname-12345 --region us-east-1
```

Update `lambda_function.py` with your bucket names:
```python
INPUT_BUCKET  = 'audio-input-yourname-12345'
OUTPUT_BUCKET = 'audio-output-yourname-12345'
```

### 2. Lambda Function

- **Runtime:** Python 3.9+
- **Timeout:** 30 seconds
- **Memory:** 128 MB
- **Handler:** `lambda_function.lambda_handler`

Upload `lambda_code/lambda_function.py` as the function code.

### 3. IAM Permissions

Attach this inline policy to the Lambda execution role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject"],
      "Resource": [
        "arn:aws:s3:::audio-input-yourname-12345/*",
        "arn:aws:s3:::audio-output-yourname-12345/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "transcribe:StartTranscriptionJob",
        "transcribe:GetTranscriptionJob"
      ],
      "Resource": "*"
    }
  ]
}
```

### 4. API Gateway

1. Create a REST API in API Gateway
2. Add resources: `/upload`, `/status`, `/result`
3. Add methods: `POST` on `/upload`, `GET` on `/status` and `/result`
4. Enable CORS on all resources
5. Set the Lambda proxy integration on each method
6. Deploy to a stage (e.g. `prod`)
7. Update `API_ENDPOINT` in `index.html`:
```javascript
const API_ENDPOINT = 'https://<your-api-id>.execute-api.us-east-1.amazonaws.com/prod';
```

---

## Local Analysis Tool

Use `parse_transcription.py` to analyze raw Transcribe JSON files downloaded from S3:

```bash
python parse_transcription.py transcription-result.json
```

**Output includes:**
- Full transcript text
- Speaker-separated segments with `[HH:MM:SS - HH:MM:SS]` timestamps
- Confidence analysis: average, min, max per word, total word count

---

## Supported Audio Formats

| Format | Extension | AWS Media Format |
|---|---|---|
| MP3 | `.mp3` | `mp3` |
| WAV | `.wav` | `wav` |
| M4A | `.m4a` | `mp4` |
| MP4 | `.mp4` | `mp4` |
| FLAC | `.flac` | `flac` |
| OGG | `.ogg` | `ogg` |
| WebM (recorded) | `.webm` | `mp3` (fallback) |

---

## Use Cases

| Industry | Use Case |
|---|---|
| 🏢 Business | Meeting recordings → searchable text minutes |
| 🎙️ Podcasting | Auto-generate episode transcripts |
| ⚖️ Legal | Deposition and hearing transcription |
| 🎓 Education | Lecture notes and video captions |
| 🏥 Healthcare | Doctor-patient consultation notes |
| 📞 Call Centers | Customer call transcription and review |

---

## Running Locally

Open `index.html` directly in any modern browser — no build step needed. Update the `API_ENDPOINT` constant to point to your deployed API Gateway URL.

```javascript
const API_ENDPOINT = 'https://<your-api-id>.execute-api.us-east-1.amazonaws.com/prod';
```

For the live recording feature, the browser requires HTTPS or `localhost` to access the microphone (MediaRecorder API security requirement).

---

## Developer

**Sowmya Maakam** — [@Sowmyamaakam](https://github.com/Sowmyamaakam)
