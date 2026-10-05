async def test_health_reports_server_and_database_ok(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


async def test_app_info_is_public_and_comes_from_settings(client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "admin_email", "admin@example.com")
    response = await client.get("/api/app-info")  # not signed in
    assert response.status_code == 200
    assert response.json() == {"adminEmail": "admin@example.com"}
