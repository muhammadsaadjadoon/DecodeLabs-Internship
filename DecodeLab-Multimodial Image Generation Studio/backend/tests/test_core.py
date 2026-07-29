from fastapi.testclient import TestClient
from main import app, init_db

client = TestClient(app)

def test_health():
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['ok'] is True

def test_auth_register_login_settings():
    email = 'testuser_prismora@example.com'
    r = client.post('/api/auth/register', json={'name':'Test User','email':email,'password':'password123'})
    assert r.status_code in (200, 409)
    client.post('/api/auth/logout')
    r = client.post('/api/auth/login', json={'email':email,'password':'password123'})
    assert r.status_code == 200
    r = client.get('/api/auth/me')
    assert r.status_code == 200
    r = client.get('/api/settings')
    assert r.status_code == 200

def test_index_loads():
    r = client.get('/')
    assert r.status_code == 200
    assert 'Prismora' in r.text
