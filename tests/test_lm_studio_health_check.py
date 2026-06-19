import json
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import URLError

from scripts.lm_studio_health_check import run_health_check, LM_STUDIO_URL

class TestLMStudioHealthCheck(unittest.TestCase):
    @patch('scripts.lm_studio_health_check.urllib.request.urlopen')
    def test_reports_loaded_model(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "models": [
                {
                    "key": "lfm2.5-8b-a1b",
                    "display_name": "LFM2.5 8B A1B",
                    "loaded_instances": [{"id": "lfm2.5-8b-a1b"}],
                },
                {
                    "key": "gemma-4-e2b-it",
                    "display_name": "Gemma 4 E2B",
                    "loaded_instances": [],
                },
            ]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = run_health_check()

        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.full_url, f"{LM_STUDIO_URL}/api/v1/models")
        self.assertEqual(req.method, "GET")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["code"], "LM_STUDIO_OK")
        self.assertEqual(result["active_model"], "lfm2.5-8b-a1b")
        self.assertEqual(result["active_model_display_name"], "LFM2.5 8B A1B")
        self.assertEqual(result["model_count"], 2)

    @patch('scripts.lm_studio_health_check.urllib.request.urlopen')
    def test_no_loaded_model_needs_review(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "models": [
                {
                    "key": "gemma-4-e2b-it",
                    "display_name": "Gemma 4 E2B",
                    "loaded_instances": [],
                }
            ]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = run_health_check()

        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["code"], "LM_STUDIO_NO_MODEL_LOADED")
        self.assertIsNone(result["active_model"])

    @patch('scripts.lm_studio_health_check.urllib.request.urlopen')
    def test_server_offline(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("Connection refused")

        result = run_health_check()

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["code"], "LM_STUDIO_UNAVAILABLE")

    @patch('scripts.lm_studio_health_check.urllib.request.urlopen')
    def test_malformed_response(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"not json"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = run_health_check()

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["code"], "LM_STUDIO_RESPONSE_INVALID")

if __name__ == '__main__':
    unittest.main()
