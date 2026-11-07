"""HTTP routing and request-boundary checks; no model requests in these tests."""
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
import threading
import unittest

from veran_advisor.demo import APP_ID, Handler


class DemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = response.status, response.read()
        connection.close()
        return result

    def test_health_and_form_are_served(self):
        status, body = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["app"], APP_ID)
        status, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("生成三条候选话术", body.decode("utf-8"))

    def test_private_files_cannot_be_served(self):
        status, _ = self.request("GET", "/report/../../private/Written_Challenge_Brief.pdf")
        self.assertEqual(status, 403)

    def test_invalid_scenario_rejected_without_inference(self):
        status, _ = self.request("POST", "/api/generate", json.dumps({"scenario": "unknown"}), {"Content-Type": "application/json"})
        self.assertEqual(status, 400)

    def test_other_origin_rejected(self):
        status, _ = self.request("POST", "/api/generate", "{}", {"Content-Type": "application/json", "Origin": "https://unrelated.example"})
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
