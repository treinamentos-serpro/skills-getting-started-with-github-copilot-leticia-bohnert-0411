"""Tests for the Mergington High School Management System API."""

import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    """Restore the in-memory activity database after each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


class TestRoot:
    def test_root_redirects_to_static_index(self):
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    def test_returns_all_activities(self):
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert len(data) == len(activities)

    def test_activity_has_expected_fields(self):
        response = client.get("/activities")
        chess = response.json()["Chess Club"]
        assert chess["description"] == "Learn strategies and compete in chess tournaments"
        assert chess["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
        assert chess["max_participants"] == 12
        assert "michael@mergington.edu" in chess["participants"]


class TestSignup:
    def test_signup_success(self):
        email = "newstudent@mergington.edu"
        response = client.post(
            "/activities/Chess Club/signup", params={"email": email}
        )
        assert response.status_code == 200
        assert response.json() == {"message": f"Signed up {email} for Chess Club"}
        assert email in activities["Chess Club"]["participants"]

    def test_signup_unknown_activity_returns_404(self):
        response = client.post(
            "/activities/Unknown Club/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_returns_400(self):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_requires_email(self):
        response = client.post("/activities/Chess Club/signup")
        assert response.status_code == 422


class TestUnregister:
    def test_unregister_success(self):
        email = "michael@mergington.edu"
        response = client.delete(
            "/activities/Chess Club/unregister", params={"email": email}
        )
        assert response.status_code == 200
        assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_unknown_activity_returns_404(self):
        response = client.delete(
            "/activities/Unknown Club/unregister",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up_returns_400(self):
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notsignedup@mergington.edu"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"


class TestSignupUnregisterFlow:
    def test_signup_then_unregister(self):
        email = "cycle@mergington.edu"
        activity = "Basketball Team"

        signup = client.post(f"/activities/{activity}/signup", params={"email": email})
        assert signup.status_code == 200
        assert email in activities[activity]["participants"]

        unregister = client.delete(
            f"/activities/{activity}/unregister", params={"email": email}
        )
        assert unregister.status_code == 200
        assert email not in activities[activity]["participants"]
