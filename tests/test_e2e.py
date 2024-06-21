from fastapi.security import oauth2
import requests


def test_posts():
    res = requests.post("http://localhost:8000/user/register", json={"username": "str", "password": "str"}, headers={"Content-Type": "application/json"})
    assert res.status_code == 201 or res.status_code == 401
    assert res.json()["message"] == "user created" or res.json()["message"] == "user already exists"

    res = requests.post("http://localhost:8000/user/login", data={"username": "str", "password": "str", "grant_type": "password"}, headers={"content-type": "application/x-www-form-urlencoded"})
    token = res.json()["access_token"]

    res = requests.post("http://localhost:8000/user/post?text=txt", headers={"Authorization": "Bearer " + token})
    assert res.status_code == 200
    assert res.json()["message"] == "Post created"

    res = requests.get("http://localhost:8000/users/post/1", headers={"Authorization": "Bearer " + token})
    assert res.json()["message"] == "txt"
    assert res.status_code == 200


def test_stats():
    res = requests.post("http://localhost:8000/user/register", json={"username": "string", "password": "string"}, headers={"Content-Type": "application/json"})
    assert res.status_code == 201 or res.status_code == 401
    assert res.json()["message"] == "user created" or res.json()["message"] == "user already exists"

    res = requests.post("http://localhost:8000/user/login", data={"username": "string", "password": "string", "grant_type": "password"}, headers={"content-type": "application/x-www-form-urlencoded"})
    token = res.json()["access_token"]

    res = requests.post("http://localhost:8000/user/post?text=txt", headers={"Authorization": "Bearer " + token})
    assert res.status_code == 200
    assert res.json()["message"] == "Post created"

    res = requests.get("http://localhost:8000/users/like/2", headers={"Authorization": "Bearer " + token})
    assert res.status_code == 200
    assert res.json()["message"] == "post liked"

    res = requests.get("http://localhost:8000/users/post/2", headers={"Authorization": "Bearer " + token})
    assert res.json()["message"] == "txt"
    assert res.status_code == 200

    res = requests.get("http://localhost:8000/stats/post/2", headers={"Authorization": "Bearer " + token})
    assert res.json()["message"] == "Post id: 2 Likes: 1 Views: 1"
    assert res.status_code == 200
