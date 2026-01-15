"""Integration tests for TUS upload flow."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.main import app
from src.app.core.database import Base
from src.app.models import Upload, Asset


@pytest.fixture(scope="function")
def test_db():
    """Create test database."""
    engine = create_engine("postgresql://test:test@localhost:5432/test_upload_service")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create test client with test database."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Generate valid JWT auth headers for testing."""
    # TODO: Generate actual JWT token
    return {
        "Authorization": "Bearer test-jwt-token",
    }


class TestTUSUploadFlow:
    """Test complete TUS upload flow."""

    def test_tus_options_returns_capabilities(self, client):
        """OPTIONS request should return TUS capabilities."""
        response = client.options("/api/v1/files/")
        
        assert response.status_code == 204
        assert response.headers["Tus-Resumable"] == "1.0.0"
        assert response.headers["Tus-Version"] == "1.0.0"
        assert "Tus-Extension" in response.headers
        assert "Tus-Max-Size" in response.headers

    def test_create_upload_session(self, client, auth_headers):
        """POST should create upload session and return Location header."""
        payload = {
            "filename": "test-image.jpg",
            "mime_type": "image/jpeg",
        }
        
        headers = {
            **auth_headers,
            "Upload-Length": "1048576",  # 1MB
            "Tus-Resumable": "1.0.0",
        }
        
        response = client.post("/api/v1/files/", json=payload, headers=headers)
        
        assert response.status_code == 201
        assert "Location" in response.headers
        assert response.headers["Tus-Resumable"] == "1.0.0"
        
        # Extract upload ID from Location
        upload_url = response.headers["Location"]
        upload_id = upload_url.split("/")[-1]
        assert upload_id

    def test_create_upload_validates_mime_type(self, client, auth_headers):
        """POST with invalid MIME type should fail."""
        payload = {
            "filename": "malware.exe",
            "mime_type": "application/x-msdownload",
        }
        
        headers = {
            **auth_headers,
            "Upload-Length": "1048576",
            "Tus-Resumable": "1.0.0",
        }
        
        response = client.post("/api/v1/files/", json=payload, headers=headers)
        
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"].lower()

    def test_create_upload_validates_file_size(self, client, auth_headers):
        """POST with file size exceeding limit should fail."""
        payload = {
            "filename": "huge-file.jpg",
            "mime_type": "image/jpeg",
        }
        
        headers = {
            **auth_headers,
            "Upload-Length": str(6 * 1024 * 1024 * 1024),  # 6GB
            "Tus-Resumable": "1.0.0",
        }
        
        response = client.post("/api/v1/files/", json=payload, headers=headers)
        
        assert response.status_code == 413

    def test_upload_chunk_increments_offset(self, client, auth_headers):
        """PATCH should upload chunk and return new offset."""
        # First create upload session
        create_payload = {
            "filename": "test-image.jpg",
            "mime_type": "image/jpeg",
        }
        
        create_headers = {
            **auth_headers,
            "Upload-Length": "1000",
            "Tus-Resumable": "1.0.0",
        }
        
        create_response = client.post(
            "/api/v1/files/",
            json=create_payload,
            headers=create_headers,
        )
        
        upload_id = create_response.headers["Location"].split("/")[-1]
        
        # Upload first chunk
        chunk_data = b"x" * 500  # 500 bytes
        
        patch_headers = {
            **auth_headers,
            "Upload-Offset": "0",
            "Content-Type": "application/offset+octet-stream",
            "Tus-Resumable": "1.0.0",
        }
        
        patch_response = client.patch(
            f"/api/v1/files/{upload_id}",
            content=chunk_data,
            headers=patch_headers,
        )
        
        assert patch_response.status_code == 204
        assert patch_response.headers["Upload-Offset"] == "500"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
