import json
from unittest.mock import patch

from django.test import TestCase

from .services import AssistantError


class IndexViewTests(TestCase):
    def test_get_renders_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")

    @patch("chat.views.ask_question", return_value="42")
    def test_post_shows_answer(self, mock_ask):
        response = self.client.post("/", {"question": "What is the answer?"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "42")
        mock_ask.assert_called_once_with("What is the answer?")

    @patch("chat.views.ask_question", side_effect=AssistantError("no key"))
    def test_post_shows_error(self, mock_ask):
        response = self.client.post("/", {"question": "hi"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no key")


class ApiAskTests(TestCase):
    @patch("chat.views.ask_question", return_value="An answer.")
    def test_valid_question(self, mock_ask):
        response = self.client.post(
            "/api/ask/",
            data=json.dumps({"question": "Hello?"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"question": "Hello?", "answer": "An answer."}
        )

    def test_missing_question(self):
        response = self.client.post(
            "/api/ask/", data="{}", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_json(self):
        response = self.client.post(
            "/api/ask/", data="not json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_get_not_allowed(self):
        response = self.client.get("/api/ask/")
        self.assertEqual(response.status_code, 405)

    @patch("chat.views.ask_question", side_effect=AssistantError("upstream down"))
    def test_upstream_error_returns_502(self, mock_ask):
        response = self.client.post(
            "/api/ask/",
            data=json.dumps({"question": "Hello?"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 502)
