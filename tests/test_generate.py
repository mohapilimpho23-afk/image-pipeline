"""
Unit tests for the pure logic in lambda/generate_upload_url.py.

These test file extension parsing and object key generation directly,
with no AWS calls involved.

Run with:
    pytest tests/test_generate_upload_url.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))

from generate_upload_url import parse_file_extension, generate_object_key


def test_parse_file_extension_from_valid_body():
    event = {'body': '{"fileType": "png"}'}
    assert parse_file_extension(event) == 'png'


def test_parse_file_extension_defaults_when_type_missing():
    event = {'body': '{}'}
    assert parse_file_extension(event) == 'jpg'


def test_parse_file_extension_defaults_on_malformed_json():
    event = {'body': 'this is not valid json'}
    assert parse_file_extension(event) == 'jpg'


def test_parse_file_extension_defaults_when_no_body_key():
    event = {}
    assert parse_file_extension(event) == 'jpg'


def test_parse_file_extension_defaults_when_type_is_empty_string():
    event = {'body': '{"fileType": ""}'}
    assert parse_file_extension(event) == 'jpg'


def test_generate_object_key_has_correct_extension():
    key = generate_object_key('png')
    assert key.endswith('.png')


def test_generate_object_key_is_unique_each_call():
    key1 = generate_object_key('jpg')
    key2 = generate_object_key('jpg')
    assert key1 != key2


def test_generate_object_key_looks_like_a_uuid_plus_extension():
    key = generate_object_key('jpg')
    name_part = key.rsplit('.', 1)[0]
    # A UUID4 string is 36 characters long (32 hex digits + 4 hyphens)
    assert len(name_part) == 36