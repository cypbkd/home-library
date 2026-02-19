from pathlib import Path
import sys
import unittest
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


class LambdaScanIsbnTests(unittest.TestCase):
    def setUp(self):
        app_lambda.app.config["TESTING"] = True
        templates_dir = str(Path(__file__).resolve().parents[1] / "templates")
        if templates_dir not in app_lambda.app.jinja_loader.searchpath:
            app_lambda.app.jinja_loader.searchpath.append(templates_dir)
        self.client = app_lambda.app.test_client()
        with self.client.session_transaction() as session:
            session["_user_id"] = "user-123"
            session["_fresh"] = True

    def test_scan_isbn_success(self):
        with patch.object(
            app_lambda.DynamoDBUser,
            "get_by_id",
            staticmethod(lambda _user_id: {"user_id": "user-123", "username": "tester", "email": "t@example.com"}),
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
            response = self.client.post("/scan_isbn", json={"isbn": "978-1234567890"})
            body = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertTrue(body["success"])
            self.assertEqual(body["isbn"], "9781234567890")

    def test_scan_isbn_from_photo_value(self):
        # ISBN visible in provided photo: 978-0-671-02703-2
        with patch.object(
            app_lambda.DynamoDBUser,
            "get_by_id",
            staticmethod(lambda _user_id: {"user_id": "user-123", "username": "tester", "email": "t@example.com"}),
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
            response = self.client.post("/scan_isbn", json={"isbn": "978-0-671-02703-2"})
            body = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertTrue(body["success"])
            self.assertEqual(body["isbn"], "9780671027032")

    def test_scan_isbn_rejects_missing_isbn(self):
        with patch.object(
            app_lambda.DynamoDBUser,
            "get_by_id",
            staticmethod(lambda _user_id: {"user_id": "user-123", "username": "tester", "email": "t@example.com"}),
        ):
            response = self.client.post("/scan_isbn", json={})
            body = response.get_json()

            self.assertEqual(response.status_code, 400)
            self.assertFalse(body["success"])
            self.assertIn("isbn", body["message"].lower())

    def test_edit_book_form_posts_to_user_book_id(self):
        with patch.object(
            app_lambda.DynamoDBUser,
            "get_by_id",
            staticmethod(lambda _user_id: {"user_id": "user-123", "username": "tester", "email": "t@example.com"}),
        ), patch.object(
            app_lambda.DynamoDBUserBook,
            "get_by_id",
            staticmethod(
                lambda _user_book_id: {
                    "user_book_id": "ub-1",
                    "user_id": "user-123",
                    "book_id": "book-1",
                    "status": "to-read",
                    "rating": None,
                }
            ),
        ), patch.object(
            app_lambda.DynamoDBBook,
            "get_by_id",
            staticmethod(
                lambda _book_id: {
                    "book_id": "book-1",
                    "isbn": "9781234567890",
                    "title": "Test Book",
                    "author": "Test Author",
                }
            ),
        ):
            response = self.client.get("/edit_book/ub-1")
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('action="/edit_book/ub-1"', html)


if __name__ == "__main__":
    unittest.main()
