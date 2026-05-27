import asyncio
import copy

import httpx
import pytest

import src.app as app_module

ORIGINAL_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    app_module.activities = copy.deepcopy(ORIGINAL_ACTIVITIES)
    yield


async def send_request(method: str, url: str, **kwargs) -> httpx.Response:
    transport = httpx.ASGITransport(app=app_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, url, **kwargs)


def test_root_redirects_to_index():
    # Arrange
    response = asyncio.run(send_request("GET", "/", follow_redirects=False))

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_data():
    # Arrange
    response = asyncio.run(send_request("GET", "/activities"))

    # Assert
    assert response.status_code == 200
    assert response.json() == ORIGINAL_ACTIVITIES


def test_signup_for_activity_success():
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    response = asyncio.run(send_request("POST", f"/activities/{activity_name}/signup", params={"email": email}))

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_duplicate_returns_400():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = asyncio.run(send_request("POST", f"/activities/{activity_name}/signup", params={"email": email}))

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_nonexistent_activity_returns_404():
    # Arrange
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"

    response = asyncio.run(send_request("POST", f"/activities/{activity_name}/signup", params={"email": email}))

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_success():
    # Arrange
    activity_name = "Basketball Team"
    email = "alex@mergington.edu"

    response = asyncio.run(send_request("DELETE", f"/activities/{activity_name}/participants", params={"email": email}))

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_non_participant_returns_404():
    # Arrange
    activity_name = "Basketball Team"
    email = "nobody@mergington.edu"

    response = asyncio.run(send_request("DELETE", f"/activities/{activity_name}/participants", params={"email": email}))

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in activity"
