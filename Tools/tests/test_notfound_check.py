import pytest
import os
import sys
import json
import mock
import boto3
from moto import mock_sns
from tools import notfound_check, logger

log = logger.setup_test_logger()

NOTFOUND_TABLE = 'notfound-unittest'


@mock.patch("tools.notfound_check.send_msg", mock.MagicMock(return_value=True))
class TestHandler:
    def test_alert(self, api_base_event, monkeypatch, notfound_mock):
        monkeypatch.setitem(os.environ, 'NOTFOUND_TABLE_NAME', NOTFOUND_TABLE)
        monkeypatch.setitem(os.environ, 'TOPIC_ARN', 'arn:aws:sns:eu-west-1:123456789012:NotFound-Item-Check-Alerts')

        response = notfound_check.handler(api_base_event, None)
        assert response['statusCode'] == 200
        assert response['headers'] == {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}

        body = json.loads(response['body'])
        assert body['items'] == 1, "Number of items was not as expected."
        assert body['alert_sent'], "Alert was sent."

    def test_no_alert(self, api_base_event, monkeypatch, empty_notfound_mock):
        monkeypatch.setitem(os.environ, 'NOTFOUND_TABLE_NAME', NOTFOUND_TABLE)
        monkeypatch.setitem(os.environ, 'TOPIC_ARN', 'arn:aws:sns:eu-west-1:123456789012:NotFound-Item-Check-Alerts')

        response = notfound_check.handler(api_base_event, None)
        assert response['statusCode'] == 200
        assert response['headers'] == {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}

        body = json.loads(response['body'])
        assert body['items'] == 0, "Number of items was not as expected."
        assert not body['alert_sent'], "Alert was not sent."


class TestGetItems:
    def test_get_items_from_empty_table(self, empty_notfound_mock):
        item_count = notfound_check.get_item_count(NOTFOUND_TABLE)
        assert item_count == 0, "Notfound table was not empty"

    def test_get_items_from_non_empty_table(self, notfound_mock):
        item_count = notfound_check.get_item_count(NOTFOUND_TABLE)
        assert item_count == 1, "Notfound table did not contain 1 item"


@mock_sns
def test_send_msg():
    sns = boto3.client('sns')
    response = sns.create_topic(
        Name='test-topic',
        Attributes={
            'DisplayName': 'NotFound Alert'
        }
    )

    topic_arn = response['TopicArn']
    assert notfound_check.send_msg(topic_arn, 2)
