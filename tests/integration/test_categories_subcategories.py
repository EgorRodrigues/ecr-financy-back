from fastapi.testclient import TestClient
from uuid import uuid4

# Categories Tests

def test_create_category(client: TestClient):
    payload = {
        "name": "Food",
        "description": "Daily expenses",
        "active": True
    }
    response = client.post("/categories/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Food"
    assert "id" in data
    return data["id"]

def test_list_categories(client: TestClient):
    client.post("/categories/", json={"name": "Transport"})
    response = client.get("/categories/")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_get_category(client: TestClient):
    # Create
    res = client.post("/categories/", json={"name": "Health"})
    cat_id = res.json()["id"]
    
    # Get
    response = client.get(f"/categories/{cat_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Health"

def test_update_category(client: TestClient):
    # Create
    res = client.post("/categories/", json={"name": "Update Me"})
    cat_id = res.json()["id"]
    
    # Update
    response = client.put(f"/categories/{cat_id}", json={"name": "Updated"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"

def test_delete_category(client: TestClient):
    # Create
    res = client.post("/categories/", json={"name": "Delete Me"})
    cat_id = res.json()["id"]
    
    # Delete
    response = client.delete(f"/categories/{cat_id}")
    assert response.status_code == 200
    
    # Verify
    assert client.get(f"/categories/{cat_id}").status_code == 404

# Subcategories Tests

def test_create_subcategory(client: TestClient):
    # Need a category first
    cat_res = client.post("/categories/", json={"name": "Parent Cat"})
    cat_id = cat_res.json()["id"]
    
    payload = {
        "category_id": cat_id,
        "name": "Sub Cat",
        "description": "Child",
        "active": True
    }
    response = client.post("/subcategories/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Sub Cat"
    assert data["category_id"] == cat_id
    return cat_id, data["id"]

def test_list_subcategories_by_category(client: TestClient):
    cat_id, _ = test_create_subcategory(client)
    
    response = client.get(f"/subcategories/{cat_id}")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["category_id"] == cat_id

def test_get_subcategory(client: TestClient):
    cat_id, sub_id = test_create_subcategory(client)
    
    response = client.get(f"/subcategories/{cat_id}/{sub_id}")
    assert response.status_code == 200
    assert response.json()["id"] == sub_id

def test_update_subcategory(client: TestClient):
    cat_id, sub_id = test_create_subcategory(client)
    
    response = client.put(f"/subcategories/{cat_id}/{sub_id}", json={"name": "Updated Sub"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Sub"

def test_move_subcategory(client: TestClient):
    # Create source category and subcategory
    cat1_res = client.post("/categories/", json={"name": "Source Cat"})
    cat1_id = cat1_res.json()["id"]
    
    sub_res = client.post("/subcategories/", json={"category_id": cat1_id, "name": "Moving Sub"})
    sub_id = sub_res.json()["id"]
    
    # Create target category
    cat2_res = client.post("/categories/", json={"name": "Target Cat"})
    cat2_id = cat2_res.json()["id"]
    
    # Move
    response = client.post(f"/subcategories/{cat1_id}/{sub_id}/move", json={"new_category_id": cat2_id})
    assert response.status_code == 200
    assert response.json()["category_id"] == cat2_id
    
    # Verify old location 404
    assert client.get(f"/subcategories/{cat1_id}/{sub_id}").status_code == 404
    # Verify new location 200
    assert client.get(f"/subcategories/{cat2_id}/{sub_id}").status_code == 200
