"""API 端到端测试：注册/登录/鉴权/日志 CRUD/筛选/统计。"""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_register_success(client):
    resp = client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "secret123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "bob"
    assert "hashed_password" not in body and "password" not in body


def test_register_duplicate_username(client, auth_headers):
    resp = client.post(
        "/api/auth/register",
        json={"username": "alice", "email": "other@example.com", "password": "secret123"},
    )
    assert resp.status_code == 400


def test_login_wrong_password(client, auth_headers):
    resp = client.post(
        "/api/auth/login", data={"username": "alice", "password": "wrong-pass"}
    )
    assert resp.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/users/me").status_code == 401
    assert client.get("/api/users/me", headers={"Authorization": "Bearer bad"}).status_code == 401


def test_me_with_token(client, auth_headers):
    resp = client.get("/api/users/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def _create_log(client, headers, level="ERROR", source="firewall", message="blocked ip"):
    return client.post(
        "/api/logs",
        headers=headers,
        json={"level": level, "source": source, "message": message},
    )


def test_log_create_and_list(client, auth_headers):
    resp = _create_log(client, auth_headers)
    assert resp.status_code == 201
    assert resp.json()["level"] == "ERROR"
    listing = client.get("/api/logs", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1


def test_log_filter_by_level_and_source(client, auth_headers):
    _create_log(client, auth_headers, level="INFO", source="app", message="started")
    _create_log(client, auth_headers, level="ERROR", source="app", message="crashed")
    _create_log(client, auth_headers, level="ERROR", source="waf", message="attack")
    errors = client.get("/api/logs?level=ERROR", headers=auth_headers).json()
    assert errors["total"] == 2
    waf = client.get("/api/logs?source=waf", headers=auth_headers).json()
    assert waf["total"] == 1
    assert waf["items"][0]["source"] == "waf"


def test_log_detail_and_delete_own(client, auth_headers):
    log_id = _create_log(client, auth_headers).json()["id"]
    detail = client.get(f"/api/logs/{log_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert client.delete(f"/api/logs/{log_id}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/logs/{log_id}", headers=auth_headers).status_code == 404


def test_log_not_accessible_by_other_user(client, auth_headers):
    log_id = _create_log(client, auth_headers).json()["id"]
    client.post(
        "/api/auth/register",
        json={"username": "carol", "email": "carol@example.com", "password": "secret123"},
    )
    token = client.post(
        "/api/auth/login", data={"username": "carol", "password": "secret123"}
    ).json()["access_token"]
    other = {"Authorization": f"Bearer {token}"}
    assert client.get(f"/api/logs/{log_id}", headers=other).status_code == 404
    assert client.delete(f"/api/logs/{log_id}", headers=other).status_code == 404
    assert client.get("/api/logs", headers=other).json()["total"] == 0


def test_stats_summary_and_trend(client, auth_headers):
    _create_log(client, auth_headers, level="INFO", message="a")
    _create_log(client, auth_headers, level="ERROR", message="b")
    _create_log(client, auth_headers, level="ERROR", message="c")
    summary = client.get("/api/stats/summary", headers=auth_headers).json()
    assert summary["total"] == 3
    by_level = {row["level"]: row["count"] for row in summary["by_level"]}
    assert by_level == {"INFO": 1, "ERROR": 2}
    trend = client.get("/api/stats/trend", headers=auth_headers).json()
    assert len(trend) == 24
    assert sum(point["count"] for point in trend) == 3
