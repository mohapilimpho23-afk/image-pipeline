"""
Tests for lambda_handler()'s orchestration logic in lambda/handler.py.

Unlike test_handler.py (which tests the pure resize_image function),
these tests mock out the S3 and SNS calls entirely, so we can verify
lambda_handler calls AWS correctly (right bucket, right key, right
message) without making any real AWS calls or needing credentials.

Run with:
    pytest tests/test_handler_orchestration.py -v
"""

import io
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))

from PIL import Image
import handler as handler_module


def make_test_image_bytes(width=400, height=400):
    image = Image.new('RGB', (width, height), (0, 0, 255))
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.read()


def make_s3_event(bucket_name, object_key):
    """Builds a minimal fake S3 event, shaped like what AWS actually sends."""
    return {
        'Records': [{
            's3': {
                'bucket': {'name': bucket_name},
                'object': {'key': object_key}
            }
        }]
    }


def test_lambda_handler_reads_from_correct_bucket_and_key():
    event = make_s3_event('limphom-image-pipeline-uploads', 'photo.jpg')
    mock_body = MagicMock()
    mock_body.read.return_value = make_test_image_bytes()

    with patch.object(handler_module.s3, 'get_object', return_value={'Body': mock_body}) as mock_get, \
         patch.object(handler_module.s3, 'put_object'), \
         patch.object(handler_module.sns, 'publish'):
        handler_module.lambda_handler(event, None)

    mock_get.assert_called_once_with(Bucket='limphom-image-pipeline-uploads', Key='photo.jpg')


def test_lambda_handler_decodes_url_encoded_filenames():
    """Filenames with spaces/special characters arrive URL-encoded from S3."""
    event = make_s3_event('limphom-image-pipeline-uploads', 'my+photo+%282%29.png')
    mock_body = MagicMock()
    mock_body.read.return_value = make_test_image_bytes()

    with patch.object(handler_module.s3, 'get_object', return_value={'Body': mock_body}) as mock_get, \
         patch.object(handler_module.s3, 'put_object'), \
         patch.object(handler_module.sns, 'publish'):
        handler_module.lambda_handler(event, None)

    mock_get.assert_called_once_with(
        Bucket='limphom-image-pipeline-uploads',
        Key='my photo (2).png'
    )


def test_lambda_handler_saves_to_processed_bucket_with_prefix():
    event = make_s3_event('limphom-image-pipeline-uploads', 'photo.jpg')
    mock_body = MagicMock()
    mock_body.read.return_value = make_test_image_bytes()

    with patch.object(handler_module.s3, 'get_object', return_value={'Body': mock_body}), \
         patch.object(handler_module.s3, 'put_object') as mock_put, \
         patch.object(handler_module.sns, 'publish'):
        handler_module.lambda_handler(event, None)

    mock_put.assert_called_once()
    call_kwargs = mock_put.call_args.kwargs
    assert call_kwargs['Bucket'] == handler_module.PROCESSED_BUCKET
    assert call_kwargs['Key'] == 'processed-photo.jpg'
    assert call_kwargs['ContentType'] == 'image/jpeg'


def test_lambda_handler_publishes_sns_notification():
    event = make_s3_event('limphom-image-pipeline-uploads', 'photo.jpg')
    mock_body = MagicMock()
    mock_body.read.return_value = make_test_image_bytes()

    with patch.object(handler_module.s3, 'get_object', return_value={'Body': mock_body}), \
         patch.object(handler_module.s3, 'put_object'), \
         patch.object(handler_module.sns, 'publish') as mock_publish:
        handler_module.lambda_handler(event, None)

    mock_publish.assert_called_once()
    call_kwargs = mock_publish.call_args.kwargs
    assert call_kwargs['TopicArn'] == handler_module.SNS_TOPIC_ARN
    assert 'photo.jpg' in call_kwargs['Message']


def test_lambda_handler_returns_200_on_success():
    event = make_s3_event('limphom-image-pipeline-uploads', 'photo.jpg')
    mock_body = MagicMock()
    mock_body.read.return_value = make_test_image_bytes()

    with patch.object(handler_module.s3, 'get_object', return_value={'Body': mock_body}), \
         patch.object(handler_module.s3, 'put_object'), \
         patch.object(handler_module.sns, 'publish'):
        result = handler_module.lambda_handler(event, None)

    assert result['statusCode'] == 200