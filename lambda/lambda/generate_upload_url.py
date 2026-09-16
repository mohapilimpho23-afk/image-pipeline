import json
import boto3
import uuid

s3 = boto3.client(
    's3',
    region_name='af-south-1',
    endpoint_url='https://s3.af-south-1.amazonaws.com'
)

UPLOAD_BUCKET = 'limphom-image-pipeline-uploads'

def lambda_handler(event, context):
    file_extension = 'jpg'

    try:
        body = json.loads(event.get('body', '{}'))
        file_extension = body.get('fileType', 'jpg')
    except Exception:
        pass

    object_key = f"{uuid.uuid4()}.{file_extension}"

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