import pytest
from fastapi.testclient import TestClient
import os
from main import app
import json

# Create a test client
client = TestClient(app)

# Create a test client
client = TestClient(app)

# Test data
test_item = {
    "name": "Pytest Pizza",
    "description": "A pizza for testing purposes.",
    "price": 13.37,
    "tags": ["test", "pizza"]
}

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Before the test, back up original menu
    with open("menu.json", "r") as f:
        original_data = json.load(f)

    yield # This is where the test runs

    # After the test, restore original menu
    with open("menu.json", "w") as f:
        json.dump(original_data, f, indent=2)

def get_admin_token():
    # In a real scenario, mock this, but for this test we'll call the endpoint
    # Ensure you have a .env file with ADMIN_USERNAME=admin and ADMIN_PASSWORD=password
    response = client.post("/token", data={"username": "admin", "password": "default_password"})
    assert response.status_code == 200
    return response.json()["access_token"]

def test_create_menu_item():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/admin/menu", headers=headers, json=test_item)
    assert response.status_code == 200
    new_item = response.json()
    assert new_item["name"] == test_item["name"]
    assert "id" in new_item

    # Verify it was written to the file
    with open("menu.json", "r") as f:
        data = json.load(f)
    assert any(item['name'] == test_item["name"] for item in data)

def test_update_menu_item():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # First, create an item to update
    create_response = client.post("/admin/menu", headers=headers, json=test_item)
    item_id = create_response.json()["id"]

    updated_data = {
        "name": "Updated Pytest Pizza",
        "description": "Updated description.",
        "price": 99.99,
        "tags": ["updated", "test"]
    }

    response = client.put(f"/admin/menu/{item_id}", headers=headers, json=updated_data)
    assert response.status_code == 200
    updated_item = response.json()
    assert updated_item["name"] == "Updated Pytest Pizza"
    assert updated_item["price"] == 99.99

    # Verify update in file
    with open("menu.json", "r") as f:
        data = json.load(f)
    assert any(item['name'] == "Updated Pytest Pizza" for item in data)
    assert not any(item['name'] == test_item["name"] for item in data)

def test_delete_menu_item():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create an item to delete
    create_response = client.post("/admin/menu", headers=headers, json=test_item)
    item_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/admin/menu/{item_id}", headers=headers)
    assert response.status_code == 200

    # Verify deletion
    with open("menu.json", "r") as f:
        data = json.load(f)
    assert not any(item['id'] == item_id for item in data)

