import json
import boto3
from PIL import Image
import io
from urllib.parse import unquote_plus

s3 = boto3.client('s3')
sns = boto3.client('sns', region_name='af-south-1')

PROCESSED_BUCKET = 'limphom-image-pipeline-processed'
SNS_TOPIC_ARN = 'arn:aws:sns:af-south-1:302432775490:image-pipeline-notifications'
MAX_SIZE = (800, 800)


def resize_image(image_bytes, max_size=MAX_SIZE):
    """Takes raw image bytes, returns resized JPEG bytes. Pure function, no AWS calls."""
    image = Image.open(io.BytesIO(image_bytes))
    image = image.convert('RGB')
    image.thumbnail(max_size)

    output_buffer = io.BytesIO()
    image.save(output_buffer, format='JPEG', quality=85)
    output_buffer.seek(0)
    return output_buffer.read()


def lambda_handler(event, context):
    record = event['Records'][0]
    source_bucket = record['s3']['bucket']['name']
    object_key = unquote_plus(record['s3']['object']['key'])

    print(f"Processing {object_key} from {source_bucket}")

    response = s3.get_object(Bucket=source_bucket, Key=object_key)
    image_data = response['Body'].read()

    resized_bytes = resize_image(image_data)

    processed_key = f"processed-{object_key}"
    s3.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=processed_key,
        Body=resized_bytes,
        ContentType='image/jpeg'
    )

    print(f"Saved processed image as {processed_key} in {PROCESSED_BUCKET}")

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject="Image Pipeline: Processing Complete",
        Message=f"Your image '{object_key}' has been processed successfully.\n\nSaved as: {processed_key}\nBucket: {PROCESSED_BUCKET}"
    )

    print("Notification sent")

    return {
        'statusCode': 200,
        'body': json.dumps(f'Processed {object_key} -> {processed_key}')
    }