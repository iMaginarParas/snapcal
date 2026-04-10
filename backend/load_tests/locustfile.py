from locust import HttpUser, task, between
import os

class FitSnapUser(HttpUser):
    # Simulate realistic user behavior with a wait time between 1 and 3 seconds
    wait_time = between(1, 3)

    @task(3)
    def health_check(self):
        """Minimal task to test API availability and rate limiting of light endpoints."""
        self.client.get("/health")

    @task(1)
    def upload_meal(self):
        """
        Simulates meal upload. 
        Note: Requires 'test_meal.jpg' to exist in the same directory as this file.
        """
        image_path = os.path.join(os.path.dirname(__file__), "test_meal.jpg")
        
        # If test image doesn't exist, we skip to avoid bulk errors in report
        if not os.path.exists(image_path):
            return

        with open(image_path, "rb") as image:
            files = {
                "file": ("test_meal.jpg", image, "image/jpeg")
            }
            # We use name parameter to group these requests in Locust UI
            self.client.post("/meals/", files=files, name="/meals (upload)")

    @task(2)
    def get_history(self):
        """Simulates viewing meal history."""
        self.client.get("/meals/", name="/meals (history)")
