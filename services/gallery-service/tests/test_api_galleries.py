"""Tests for galleries API endpoints (authenticated staff routes)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from src.app.core.auth import CurrentUser, get_current_user
from src.app.main import app
from src.app.models.gallery import Gallery
from src.app.models.sub_gallery import SubGallery


# Other workspace ID for cross-workspace tests
OTHER_WORKSPACE_ID = "00000000-0000-0000-0000-000000000999"


@pytest.fixture
def mock_current_user():
    """Return a mock authenticated user."""
    return CurrentUser(
        user_id="user-123",
        email="test@example.com",
        workspace_id="00000000-0000-0000-0000-000000000123",
        email_verified=True,
    )


@pytest.fixture
def mock_user_no_workspace():
    """Return a mock user without workspace."""
    return CurrentUser(
        user_id="user-123",
        email="test@example.com",
        workspace_id=None,
        email_verified=True,
    )


@pytest.fixture
async def auth_client(test_db_session, mock_current_user):
    """Create authenticated test client."""
    from src.app.core.database import get_db

    async def override_get_db():
        yield test_db_session

    def override_get_current_user():
        return mock_current_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def no_workspace_client(test_db_session, mock_user_no_workspace):
    """Create authenticated client without workspace."""
    from src.app.core.database import get_db

    async def override_get_db():
        yield test_db_session

    def override_get_current_user():
        return mock_user_no_workspace

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def other_workspace(test_db_session):
    """Create another workspace for cross-workspace tests."""
    await test_db_session.execute(
        text(f"""
            INSERT INTO workspaces (id, created_at, updated_at)
            VALUES ('{OTHER_WORKSPACE_ID}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING
        """)
    )
    await test_db_session.commit()
    return OTHER_WORKSPACE_ID


@pytest.mark.asyncio
class TestListGalleries:
    """Test GET /api/v1/galleries endpoint."""

    async def test_list_galleries_empty(self, auth_client: AsyncClient, test_db_session):
        """Test listing galleries when none exist."""
        response = await auth_client.get("/api/v1/galleries")

        assert response.status_code == 200
        data = response.json()
        assert data["galleries"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["has_next"] is False

    async def test_list_galleries_with_data(self, auth_client: AsyncClient, test_db_session):
        """Test listing galleries with existing galleries."""
        # Create test galleries
        gallery1 = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery One",
            status="draft",
        )
        gallery2 = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery Two",
            status="published",
        )
        test_db_session.add_all([gallery1, gallery2])
        await test_db_session.commit()

        response = await auth_client.get("/api/v1/galleries")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["galleries"]) == 2
        titles = [g["title"] for g in data["galleries"]]
        assert "Gallery One" in titles
        assert "Gallery Two" in titles

    async def test_list_galleries_pagination(self, auth_client: AsyncClient, test_db_session):
        """Test galleries pagination."""
        # Create 25 galleries
        for i in range(25):
            gallery = Gallery(
                workspace_id="00000000-0000-0000-0000-000000000123",
                title=f"Gallery {i}",
                status="draft",
            )
            test_db_session.add(gallery)
        await test_db_session.commit()

        # First page
        response = await auth_client.get("/api/v1/galleries?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["galleries"]) == 10
        assert data["total"] == 25
        assert data["has_next"] is True

        # Second page
        response = await auth_client.get("/api/v1/galleries?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["galleries"]) == 10
        assert data["has_next"] is True

        # Third page
        response = await auth_client.get("/api/v1/galleries?page=3&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["galleries"]) == 5
        assert data["has_next"] is False

    async def test_list_galleries_filter_by_status(self, auth_client: AsyncClient, test_db_session):
        """Test filtering galleries by status."""
        gallery1 = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Draft Gallery",
            status="draft",
        )
        gallery2 = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Published Gallery",
            status="published",
        )
        test_db_session.add_all([gallery1, gallery2])
        await test_db_session.commit()

        response = await auth_client.get("/api/v1/galleries?status=published")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["galleries"][0]["title"] == "Published Gallery"

    async def test_list_galleries_no_workspace(self, no_workspace_client: AsyncClient):
        """Test listing galleries without workspace returns 403."""
        response = await no_workspace_client.get("/api/v1/galleries")

        assert response.status_code == 403
        assert "workspace" in response.json()["detail"].lower()

    async def test_list_galleries_only_own_workspace(
        self, auth_client: AsyncClient, test_db_session, other_workspace
    ):
        """Test user only sees galleries from their workspace."""
        # Gallery in user's workspace
        own_gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="My Gallery",
            status="draft",
        )
        # Gallery in different workspace
        other_gallery = Gallery(
            workspace_id=other_workspace,
            title="Other Gallery",
            status="draft",
        )
        test_db_session.add_all([own_gallery, other_gallery])
        await test_db_session.commit()

        response = await auth_client.get("/api/v1/galleries")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["galleries"][0]["title"] == "My Gallery"


@pytest.mark.asyncio
class TestCreateGallery:
    """Test POST /api/v1/galleries endpoint."""

    async def test_create_gallery_success(self, auth_client: AsyncClient, test_db_session):
        """Test creating a gallery successfully."""
        response = await auth_client.post(
            "/api/v1/galleries",
            json={
                "title": "New Gallery",
                "description": "Test description",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Gallery"
        assert data["description"] == "Test description"
        assert data["status"] == "draft"
        assert data["workspace_id"] == "00000000-0000-0000-0000-000000000123"

    async def test_create_gallery_minimal(self, auth_client: AsyncClient, test_db_session):
        """Test creating a gallery with only required fields."""
        response = await auth_client.post(
            "/api/v1/galleries",
            json={"title": "Minimal Gallery"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Gallery"

    async def test_create_gallery_with_all_fields(
        self, auth_client: AsyncClient, test_db_session
    ):
        """Test creating a gallery with all optional fields."""
        response = await auth_client.post(
            "/api/v1/galleries",
            json={
                "title": "Full Gallery",
                "description": "Complete gallery",
                "client_name": "John Doe",
                "shoot_date": "2024-01-15",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Full Gallery"
        assert data["description"] == "Complete gallery"

    async def test_create_gallery_no_workspace(self, no_workspace_client: AsyncClient):
        """Test creating gallery without workspace returns 403."""
        response = await no_workspace_client.post(
            "/api/v1/galleries",
            json={"title": "Test Gallery"},
        )

        assert response.status_code == 403
        assert "workspace" in response.json()["detail"].lower()

    async def test_create_gallery_missing_title(
        self, auth_client: AsyncClient, test_db_session
    ):
        """Test creating gallery without title fails validation."""
        response = await auth_client.post(
            "/api/v1/galleries",
            json={"description": "No title"},
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestGetGallery:
    """Test GET /api/v1/galleries/{gallery_id} endpoint."""

    async def test_get_gallery_success(self, auth_client: AsyncClient, test_db_session):
        """Test getting a gallery successfully."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            description="Test description",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await auth_client.get(f"/api/v1/galleries/{gallery.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Gallery"
        assert data["description"] == "Test description"

    async def test_get_gallery_with_sub_galleries(
        self, auth_client: AsyncClient, test_db_session
    ):
        """Test getting gallery includes sub-galleries."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Parent Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        sub_gallery = SubGallery(
            gallery_id=gallery.id,
            name="Sub Gallery 1",
            sort_order=0,
            visible=True,
        )
        test_db_session.add(sub_gallery)
        await test_db_session.commit()

        response = await auth_client.get(f"/api/v1/galleries/{gallery.id}")

        assert response.status_code == 200
        data = response.json()
        assert "sub_galleries" in data
        assert len(data["sub_galleries"]) == 1
        assert data["sub_galleries"][0]["name"] == "Sub Gallery 1"

    async def test_get_gallery_not_found(self, auth_client: AsyncClient, test_db_session):
        """Test getting non-existent gallery returns 404."""
        response = await auth_client.get(
            "/api/v1/galleries/00000000-0000-0000-0000-000000000999"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_gallery_wrong_workspace(
        self, auth_client: AsyncClient, test_db_session, other_workspace
    ):
        """Test getting gallery from different workspace returns 403."""
        gallery = Gallery(
            workspace_id=other_workspace,  # Different workspace
            title="Other Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await auth_client.get(f"/api/v1/galleries/{gallery.id}")

        assert response.status_code == 403
        assert "denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestUpdateGallery:
    """Test PATCH /api/v1/galleries/{gallery_id} endpoint."""

    async def test_update_gallery_success(self, auth_client: AsyncClient, test_db_session):
        """Test updating a gallery successfully."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Original Title",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await auth_client.patch(
            f"/api/v1/galleries/{gallery.id}",
            json={"title": "Updated Title", "description": "New description"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "New description"

    async def test_update_gallery_partial(self, auth_client: AsyncClient, test_db_session):
        """Test partial update preserves other fields."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Original Title",
            description="Original description",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await auth_client.patch(
            f"/api/v1/galleries/{gallery.id}",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Original description"  # Preserved

    async def test_update_gallery_not_found(
        self, auth_client: AsyncClient, test_db_session
    ):
        """Test updating non-existent gallery returns 404."""
        response = await auth_client.patch(
            "/api/v1/galleries/00000000-0000-0000-0000-000000000999",
            json={"title": "New Title"},
        )

        assert response.status_code == 404

    async def test_update_gallery_wrong_workspace(
        self, auth_client: AsyncClient, test_db_session, other_workspace
    ):
        """Test updating gallery from different workspace returns 404."""
        gallery = Gallery(
            workspace_id=other_workspace,
            title="Other Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await auth_client.patch(
            f"/api/v1/galleries/{gallery.id}",
            json={"title": "Hacked"},
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestDeleteGallery:
    """Test DELETE /api/v1/galleries/{gallery_id} endpoint."""

    async def test_delete_gallery_success(self, auth_client: AsyncClient, test_db_session):
        """Test deleting a gallery successfully."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="To Delete",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        gallery_id = gallery.id

        response = await auth_client.delete(f"/api/v1/galleries/{gallery_id}")

        assert response.status_code == 204

        # Verify deleted
        response = await auth_client.get(f"/api/v1/galleries/{gallery_id}")
        assert response.status_code == 404

    async def test_delete_gallery_not_found(
        self, auth_client: AsyncClient, test_db_session
    ):
        """Test deleting non-existent gallery returns 404."""
        response = await auth_client.delete(
            "/api/v1/galleries/00000000-0000-0000-0000-000000000999"
        )

        assert response.status_code == 404

    async def test_delete_gallery_wrong_workspace(
        self, auth_client: AsyncClient, test_db_session, other_workspace
    ):
        """Test deleting gallery from different workspace returns 404."""
        gallery = Gallery(
            workspace_id=other_workspace,
            title="Other Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await auth_client.delete(f"/api/v1/galleries/{gallery.id}")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestPublishGallery:
    """Test POST /api/v1/galleries/{gallery_id}/publish endpoint."""

    async def test_publish_gallery_success(
        self, auth_client: AsyncClient, test_db_session
    ):
        """Test publishing a gallery successfully."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="To Publish",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await auth_client.post(f"/api/v1/galleries/{gallery.id}/publish")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"

    async def test_publish_gallery_not_found(
        self, auth_client: AsyncClient, test_db_session
    ):
        """Test publishing non-existent gallery returns 404."""
        response = await auth_client.post(
            "/api/v1/galleries/00000000-0000-0000-0000-000000000999/publish"
        )

        assert response.status_code == 404

    async def test_publish_gallery_wrong_workspace(
        self, auth_client: AsyncClient, test_db_session, other_workspace
    ):
        """Test publishing gallery from different workspace returns 404."""
        gallery = Gallery(
            workspace_id=other_workspace,
            title="Other Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await auth_client.post(f"/api/v1/galleries/{gallery.id}/publish")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestArchiveGallery:
    """Test POST /api/v1/galleries/{gallery_id}/archive endpoint."""

    async def test_archive_gallery_success(
        self, auth_client: AsyncClient, test_db_session
    ):
        """Test archiving a gallery successfully."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="To Archive",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await auth_client.post(f"/api/v1/galleries/{gallery.id}/archive")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "archived"

    async def test_archive_gallery_not_found(
        self, auth_client: AsyncClient, test_db_session
    ):
        """Test archiving non-existent gallery returns 404."""
        response = await auth_client.post(
            "/api/v1/galleries/00000000-0000-0000-0000-000000000999/archive"
        )

        assert response.status_code == 404

    async def test_archive_gallery_wrong_workspace(
        self, auth_client: AsyncClient, test_db_session, other_workspace
    ):
        """Test archiving gallery from different workspace returns 404."""
        gallery = Gallery(
            workspace_id=other_workspace,
            title="Other Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await auth_client.post(f"/api/v1/galleries/{gallery.id}/archive")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestGalleryToResponse:
    """Test _gallery_to_response helper function."""

    async def test_response_includes_all_fields(
        self, auth_client: AsyncClient, test_db_session
    ):
        """Test gallery response includes all expected fields."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Complete Gallery",
            description="Full description",
            status="published",
            photo_count=10,
            video_count=2,
            favorites_count=5,
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await auth_client.get(f"/api/v1/galleries/{gallery.id}")

        assert response.status_code == 200
        data = response.json()

        # Verify all fields present
        assert "gallery_id" in data
        assert "workspace_id" in data
        assert "title" in data
        assert "description" in data
        assert "status" in data
        assert "cover_asset_id" in data
        assert "password_protected" in data
        assert "photo_count" in data
        assert "video_count" in data
        assert "favorites_count" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Verify values
        assert data["title"] == "Complete Gallery"
        assert data["photo_count"] == 10
        assert data["video_count"] == 2
        assert data["favorites_count"] == 5
        assert data["password_protected"] is False
