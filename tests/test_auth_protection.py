import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_protected_endpoint_requires_auth():
    response = client.post("/sync/user/1")
    assert response.status_code == 401 or response.status_code == 403
    
# Para testar acesso de usuário ativo e com role, seria necessário mockar autenticação e banco.
# Este teste é apenas um exemplo de proteção básica.
