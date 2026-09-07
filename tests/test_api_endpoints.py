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
        self.assertIn("background_tasks", data["metrics"])

    def test_tasks_api(self):
        res = self.client.get("/api/tasks")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

        # Create user
        res_user = self.client.post("/api/users")
        user_id = res_user.json()["id"]

        # Trigger background reindex
        res_reindex = self.client.post(
            "/api/tasks/reindex",
            json={"user_id": user_id}
        )
        self.assertEqual(res_reindex.status_code, 200)
        task_data = res_reindex.json()
        self.assertIn("task_id", task_data)
        self.assertEqual(task_data["task_type"], "batch_reindex")

        # Query single task
        task_id = task_data["task_id"]
        res_task = self.client.get(f"/api/tasks/{task_id}")
        self.assertEqual(res_task.status_code, 200)
        self.assertEqual(res_task.json()["task_id"], task_id)

    def test_delete_conversation_and_user_api(self):
        # 1. Create user and conversation
        res_user = self.client.post("/api/users")
        self.assertEqual(res_user.status_code, 200)
        user_id = res_user.json()["id"]

        res_conv = self.client.post(
            f"/api/users/{user_id}/conversations",
            json={"title": "To be deleted"}
        )
        self.assertEqual(res_conv.status_code, 200)
        conv_id = res_conv.json()["id"]

        # 2. Delete conversation
        res_del_conv = self.client.delete(f"/api/conversations/{conv_id}")
        self.assertEqual(res_del_conv.status_code, 200)
        self.assertEqual(res_del_conv.json()["status"], "success")

        # Verify conversation is gone
        res_get_convs = self.client.get(f"/api/users/{user_id}/conversations")
        self.assertEqual(res_get_convs.status_code, 200)
        self.assertNotIn(conv_id, [c["id"] for c in res_get_convs.json()])

        # Delete non-existent conversation returns 404
        res_del_404 = self.client.delete(f"/api/conversations/{conv_id}")
        self.assertEqual(res_del_404.status_code, 404)

        # 3. Delete user
        res_del_user = self.client.delete(f"/api/users/{user_id}")
        self.assertEqual(res_del_user.status_code, 200)
        self.assertEqual(res_del_user.json()["status"], "success")

        # Verify user is gone
        res_get_user = self.client.get(f"/api/users/{user_id}")
        self.assertEqual(res_get_user.status_code, 404)

        # Delete non-existent user returns 404
        res_del_user_404 = self.client.delete(f"/api/users/{user_id}")
        self.assertEqual(res_del_user_404.status_code, 404)


if __name__ == "__main__":
    unittest.main()
