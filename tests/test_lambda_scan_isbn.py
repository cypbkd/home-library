import base64
from pathlib import Path
import sys
import unittest
from io import BytesIO
from unittest.mock import patch
import types


AWS_DIR = Path(__file__).resolve().parents[1] / "app" / "aws_lambda"
if str(AWS_DIR) not in sys.path:
    sys.path.insert(0, str(AWS_DIR))

# Stub boto3 modules so the Lambda app imports cleanly in local test environments
# without AWS SDK installed.
if "boto3" not in sys.modules:
    boto3 = types.ModuleType("boto3")

    class _DummyResource:
        def Table(self, *_args, **_kwargs):
            return object()

    class _DummyClient:
        pass

    boto3.resource = lambda *_args, **_kwargs: _DummyResource()
    boto3.client = lambda *_args, **_kwargs: _DummyClient()
    sys.modules["boto3"] = boto3

if "boto3.dynamodb.conditions" not in sys.modules:
    conditions = types.ModuleType("boto3.dynamodb.conditions")

    class _DummyCondition:
        def eq(self, *_args, **_kwargs):
            return self

        def __and__(self, _other):
            return self

    conditions.Key = lambda _name: _DummyCondition()
    conditions.Attr = lambda _name: _DummyCondition()
    sys.modules["boto3.dynamodb"] = types.ModuleType("boto3.dynamodb")
    sys.modules["boto3.dynamodb.conditions"] = conditions

import app_lambda


def _payload():
    encoded = base64.b64encode(b"fake-image-bytes").decode("utf-8")
    return {"image": f"data:image/png;base64,{encoded}"}


class LambdaScanIsbnTests(unittest.TestCase):
    def setUp(self):
        app_lambda.app.config["TESTING"] = True
        self.client = app_lambda.app.test_client()
        with self.client.session_transaction() as session:
            session["_user_id"] = "user-123"
            session["_fresh"] = True

    def test_scan_isbn_success(self):
        class FakeImage:
            mode = "RGB"

            def convert(self, mode):
                self.mode = mode
                return self

        class FakeImageModule:
            @staticmethod
            def open(_file_obj):
                return FakeImage()

        class FakeBarcode:
            data = b"9781234567890"

        with patch.object(
            app_lambda.DynamoDBUser,
            "get_by_id",
            staticmethod(lambda _user_id: {"user_id": "user-123", "username": "tester", "email": "t@example.com"}),
        ), patch.object(
            app_lambda,
            "_get_barcode_decoder",
            lambda: (BytesIO, FakeImageModule, lambda _image: [FakeBarcode()]),
        ), patch.object(
            app_lambda.DynamoDBBook,
            "get_by_isbn",
            staticmethod(lambda _isbn: None),
        ), patch.object(
            app_lambda.DynamoDBBook,
            "create",
            staticmethod(lambda isbn, title, author: {"book_id": "book-1", "isbn": isbn, "title": title, "author": author}),
        ), patch.object(
            app_lambda.DynamoDBUserBook,
            "get",
            staticmethod(lambda _uid, _bid: None),
        ), patch.object(
            app_lambda.DynamoDBUserBook,
            "create",
            staticmethod(lambda *_args, **_kwargs: {"user_book_id": "ub-1"}),
        ), patch.object(
            app_lambda,
            "fetch_book_metadata_async",
            lambda _user_book_id: None,
        ):
            response = self.client.post("/scan_isbn", json=_payload())
            body = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertTrue(body["success"])
            self.assertEqual(body["isbn"], "9781234567890")

    def test_scan_isbn_returns_503_when_dependencies_missing(self):
        with patch.object(
            app_lambda.DynamoDBUser,
            "get_by_id",
            staticmethod(lambda _user_id: {"user_id": "user-123", "username": "tester", "email": "t@example.com"}),
        ), patch.object(
            app_lambda,
            "_get_barcode_decoder",
            lambda: (_ for _ in ()).throw(ImportError("missing barcode libs")),
        ):
            response = self.client.post("/scan_isbn", json=_payload())
            body = response.get_json()

            self.assertEqual(response.status_code, 503)
            self.assertFalse(body["success"])
            self.assertIn("dependencies", body["message"].lower())


if __name__ == "__main__":
    unittest.main()
