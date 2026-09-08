# Omni Flash 10-second API

Use the user's current API key from the environment variable `OMNI_API_KEY` or `UPDRAMA_API_KEY`. Never place the key in a prompt file, manifest, log, or final response.

Base URL: `https://api.lk888.ai`

## Create

`POST /v1/media/generate`

Headers:

```text
Authorization: Bearer $OMNI_API_KEY
Content-Type: application/json
```

Body for text-to-video:

```json
{
  "model": "omni_flash-10s",
  "params": {"aspect_ratio": "9:16"},
  "prompt": "FULL ENGLISH T2V PROMPT"
}
```

Do not add `images` for this workflow. The model always generates a 10-second 720P clip. A successful response normally contains `data.task_id`.

## Status

`GET /v1/media/status?task_id={task_id}` with the same bearer header.

Use `is_final` and `state`, not the Chinese display fields. Poll every 3–5 seconds. `state` values are `pending`, `running`, `success`, or `failed`. On `success`, download `result_url`. On `failed`, record the error and never POST the same job again.

## One-submit rule

Persist a manifest before polling. Key it by the stable `job_id`, not by filename alone. If a POST returns a task ID, that job is submitted forever even if polling or downloading later fails. If the POST itself times out and no response is known, mark `submission_unknown_no_retry` to prevent accidental duplicate generation.

## Output

Save MP4 files to `/Users/<user>/Desktop/wibly-videos/` by default. Validate with ffprobe: video stream must be 720x1280 and duration approximately 10 seconds.
