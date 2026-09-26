import os
import sys
import unittest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv()

from app.main import app
from app.core.config import settings

client = TestClient(app)

class TestProductionIntegrations(unittest.TestCase):
    def setUp(self):
        # Two distinct coach tokens simulating Coach A and Coach B
        self.coach_a_headers = {"Authorization": "Bearer mock-token-coach_alpha_uuid_101"}
        self.coach_b_headers = {"Authorization": "Bearer mock-token-coach_beta_uuid_202"}

    def test_01_multi_tenant_isolation(self):
        """Verify Coach A cannot see Coach B data across all core entities."""
        # 1. Coach A creates a client
        client_payload = {
            "name": "Athlete Alpha",
            "email": "alpha@example.com",
            "goal": "Olympic Weightlifting",
            "target_cals": 2600
        }
        res_a = client.post("/api/coach/clients", json=client_payload, headers=self.coach_a_headers)
        self.assertEqual(res_a.status_code, 200)
        client_a = res_a.json().get("data", {})
        self.assertEqual(client_a.get("coach_id"), "coach_alpha_uuid_101")

        # 2. Coach B fetches clients — should NOT contain Coach A's client
        res_b_list = client.get("/api/coach/clients", headers=self.coach_b_headers)
        self.assertEqual(res_b_list.status_code, 200)
        coach_b_clients = res_b_list.json().get("data", [])
        coach_b_client_ids = [c["id"] for c in coach_b_clients]
        self.assertNotIn(client_a["id"], coach_b_client_ids, "CRITICAL: Coach B can see Coach A's client!")

        # 3. Coach A creates a session
        session_payload = {
            "client_name": "Athlete Alpha",
            "title": "Clean & Jerk Technique",
            "date": "2026-10-01",
            "time": "09:00 AM",
            "duration": "60 min"
        }
        res_sess = client.post("/api/coach/sessions", json=session_payload, headers=self.coach_a_headers)
        self.assertEqual(res_sess.status_code, 200)
        sess_a = res_sess.json().get("data", {})
        self.assertEqual(sess_a.get("coach_id"), "coach_alpha_uuid_101")

        # Coach B fetches sessions — should NOT contain Coach A's session
        res_b_sess = client.get("/api/coach/sessions", headers=self.coach_b_headers)
        self.assertEqual(res_b_sess.status_code, 200)
        coach_b_sess_ids = [s["id"] for s in res_b_sess.json().get("data", [])]
        self.assertNotIn(sess_a["id"], coach_b_sess_ids, "CRITICAL: Coach B can see Coach A's session!")

        # 4. Coach A creates a product
        product_payload = {
            "title": "12-Week Peaking Protocol",
            "price": 4999.0,
            "currency": "INR",
            "duration": "12 weeks"
        }
        res_prod = client.post("/api/coach/products", json=product_payload, headers=self.coach_a_headers)
        self.assertEqual(res_prod.status_code, 200)
        prod_a = res_prod.json().get("data", {})
        self.assertEqual(prod_a.get("coach_id"), "coach_alpha_uuid_101")

        # Coach B fetches products — should NOT contain Coach A's product
        res_b_prod = client.get("/api/coach/products", headers=self.coach_b_headers)
        self.assertEqual(res_b_prod.status_code, 200)
        coach_b_prod_ids = [p["id"] for p in res_b_prod.json().get("data", [])]
        self.assertNotIn(prod_a["id"], coach_b_prod_ids, "CRITICAL: Coach B can see Coach A's product!")

    def test_02_gemini_ai_workout_generation(self):
        """Verify real Gemini AI generation returns structured, non-static workout data."""
        payload = {
            "goal": "Hyrox Functional Conditioning",
            "durationMinutes": 45,
            "level": "Advanced",
            "prompt": "Create high intensity intervals focusing on ski-erg, sled push, and burpees",
            "equipment": "Commercial Gym"
        }
        res = client.post("/api/coach/ai/generate-workout", json=payload, headers=self.coach_a_headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body.get("success"))
        data = body.get("data", {})
        self.assertIn("exercises", data)
        self.assertTrue(len(data["exercises"]) > 0, "AI returned 0 exercises!")
        first_ex = data["exercises"][0]
        self.assertIn("name", first_ex)
        self.assertIn("sets", first_ex)
        print(f"[TEST AI OK] Generated: {data.get('name')} with {len(data['exercises'])} exercises.")

    def test_03_payment_security_and_plans(self):
        """Verify payment catalog and cryptographic webhook security."""
        # 1. Plans catalog
        res = client.get("/api/payments/plans")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("plans", body)
        self.assertTrue(len(body["plans"]) >= 3)

        # 2. Webhook without signature when secret is set should be rejected
        import hmac, hashlib
        settings.RAZORPAY_WEBHOOK_SECRET = "test_webhook_secret_key_123"
        webhook_body = b'{"event": "payment.captured", "payload": {}}'

        # Invalid/missing signature
        res_bad = client.post("/api/payments/webhook", content=webhook_body)
        self.assertEqual(res_bad.status_code, 400, "Webhook allowed request without signature!")

        # Valid HMAC signature
        valid_sig = hmac.new("test_webhook_secret_key_123".encode("utf-8"), webhook_body, hashlib.sha256).hexdigest()
        res_good = client.post("/api/payments/webhook", content=webhook_body, headers={"X-Razorpay-Signature": valid_sig})
        self.assertEqual(res_good.status_code, 200)
        self.assertEqual(res_good.json().get("status"), "ok")

    def test_04_client_telemetry_endpoint(self):
        """Verify SabTrack client telemetry endpoint responds with valid schema."""
        res = client.get("/api/coach/client/test_client_id_999/telemetry")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body.get("success"))
        self.assertIn("data", body)
        self.assertIn("client_id", body["data"])

if __name__ == "__main__":
    unittest.main()
