# Image Pipeline

A serverless image processing pipeline built on AWS. Upload an image through the web page, and it's automatically resized, converted, and stored in the cloud — with an email notification when it's done.

No servers to manage, no manual steps, and it costs nothing when idle.

## How it works

1. You drag an image onto the upload page.
2. The page asks an API for a temporary, secure upload URL.
3. The browser uploads the file directly to an S3 bucket using that URL.
4. The upload automatically triggers a Lambda function.
5. That function resizes the image (max 800x800) and converts it to JPEG using Pillow.
6. The result is saved to a second S3 bucket.
7. An email notification is sent confirming the processing is complete.

![Architecture diagram](docs/architecture-diagram.png)

## Tech stack

| Piece | AWS Service |
|---|---|
| Frontend | Static HTML/JS page, hosted locally |
| API | API Gateway (HTTP API) |
| Compute | AWS Lambda (Python 3.12) |
| Image processing | Pillow (via Lambda Layer) |
| Storage | Amazon S3 (two buckets: uploads, processed) |
| Notifications | Amazon SNS (email) |
| Access control | IAM (least-privilege roles per function) |
| Region | af-south-1 (Cape Town) |

## Project structure

```
image-pipeline/
├── docs/
│   └── architecture-diagram.png
├── frontend/
│   └── index.html          # Upload page (drag-and-drop)
├── lambda/
│   ├── handler.py           # Resizes images, triggered by S3 upload
│   └── generate_upload_url.py  # Returns a pre-signed S3 upload URL
├── README.md
└── .gitignore
```

## Architecture

**Upload flow:**
`Browser → API Gateway → generate-upload-url (Lambda) → S3 (uploads bucket)`

**Processing flow (triggered automatically):**
`S3 (uploads bucket) → image-pipeline-processor (Lambda) → S3 (processed bucket) → SNS → Email`

The browser never touches AWS credentials directly. Instead, it requests a short-lived, upload-only pre-signed URL from a Lambda function behind API Gateway, then uploads straight to S3 with that URL.

## Setting it up yourself

1. **Create two S3 buckets** — one for uploads, one for processed images.
2. **Create the `image-pipeline-processor` Lambda function** (Python 3.12), using the code in `lambda/handler.py`. Attach the [Klayers Pillow layer](https://github.com/keithrozario/Klayers) for your region and Python version. Set a 30-second timeout and 256 MB memory.
3. **Add an S3 trigger** on the uploads bucket, pointing at this function.
4. **Create the `generate-upload-url` Lambda function**, using the code in `lambda/generate_upload_url.py`.
5. **Create an HTTP API** in API Gateway with a `POST /upload-url` route pointing at that function. Enable CORS.
6. **Enable CORS on the uploads S3 bucket** (Permissions → CORS) to allow browser uploads.
7. **Create an SNS topic** and subscribe your email to it.
8. **Set up IAM roles** for each Lambda function with only the permissions it needs (see below).
9. Update the `API_URL`, bucket names, and SNS topic ARN in the code to match your own resources.
10. Open `frontend/index.html` in a browser and try it out.

## IAM permissions (least privilege)

Each Lambda function has its own scoped policy rather than broad account access:

- **`image-pipeline-processor`**: `s3:GetObject` on the uploads bucket, `s3:PutObject` on the processed bucket, `sns:Publish` on the notification topic, plus basic CloudWatch logging.
- **`generate-upload-url`**: `s3:PutObject` on the uploads bucket, plus basic CloudWatch logging.

Both started out with broader managed policies (`AdministratorAccess` / `AmazonS3FullAccess`) to speed up initial development, then were locked down once the pipeline was proven working end-to-end.

## Notable challenges

- **Region-specific endpoints**: `af-south-1` (Cape Town) requires pre-signed URLs to be generated against a region-specific S3 endpoint, not the default global one. This showed up first as a confusing browser CORS error before being traced back to an `IllegalLocationConstraintException` via direct `curl` testing.
- **URL-encoded S3 keys**: filenames with spaces or special characters arrive URL-encoded in S3 event payloads and need to be decoded (`urllib.parse.unquote_plus`) before use.
- **Lambda timeouts**: the default 3-second timeout isn't enough for image processing; bumped to 30 seconds with 256 MB memory.

## Future improvements

- CI/CD pipeline to auto-deploy Lambda code on push, instead of manual console deploys.
- Thumbnail size options / multiple output sizes.
- A hosted frontend (e.g. S3 static website or CloudFront) instead of running locally.
- Image format validation and virus/malware scanning before processing.

YOUTUBE DEMO : https://www.youtube.com/watch?v=WERt06c1-Ck
## Author

Limpho Mohapi
