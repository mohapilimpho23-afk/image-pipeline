import json
import boto3
import uuid

s3 = boto3.client(
    's3',
    region_name='af-south-1',
    endpoint_url='https://s3.af-south-1.amazonaws.com'
)

UPLOAD_BUCKET = 'limphom-image-pipeline-uploads'
DEFAULT_EXTENSION = 'jpg'


def parse_file_extension(event):
    """Extracts the file extension from the request body, defaulting to jpg
    if it's missing or the body is malformed. Pure function, no AWS calls."""
    try:
        body = json.loads(event.get('body', '{}'))
        extension = body.get('fileType', DEFAULT_EXTENSION)
        return extension if extension else DEFAULT_EXTENSION
    except Exception:
        return DEFAULT_EXTENSION


def generate_object_key(file_extension):
    """Builds a unique S3 object key for the upload. Pure function, no AWS calls."""
    return f"{uuid.uuid4()}.{file_extension}"


def lambda_handler(event, context):
    file_extension = parse_file_extension(event)
    object_key = generate_object_key(file_extension)

    presigned_url = s3.generate_presigned_url(
        'put_object',
        Params={'Bucket': UPLOAD_BUCKET, 'Key': object_key},
        ExpiresIn=300
    )

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'uploadUrl': presigned_url,
            'key': object_key
        })
    }