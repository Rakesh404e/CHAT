import unittest
import os
import sys

app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi.testclient import TestClient
from api.main import app


class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_and_health(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("status", res.json())

        res_health = self.client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json(), {"status": "ok"})

    def test_users_api(self):
        res = self.client.post("/api/users")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("id", data)
        user_id = data["id"]

        res_get = self.client.get(f"/api/users/{user_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["id"], user_id)

    def test_conversations_api(self):
        res_user = self.client.post("/api/users")
        user_id = res_user.json()["id"]

        res_conv = self.client.post(
            f"/api/users/{user_id}/conversations",
            json={"title": "Test Session"}
        )
        self.assertEqual(res_conv.status_code, 200)
        conv_id = res_conv.json()["id"]
        self.assertEqual(res_conv.json()["title"], "Test Session")

        res_list = self.client.get(f"/api/users/{user_id}/conversations")
        self.assertEqual(res_list.status_code, 200)
        self.assertTrue(len(res_list.json()) >= 1)

    def test_observability_api(self):
        res = self.client.get("/api/observability/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("metrics", data)
        self.assertIn("llm", data["metrics"])


if __name__ == "__main__":
    unittest.main()
