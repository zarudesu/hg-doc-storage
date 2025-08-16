"""
Basic API tests for 1C Contract Service
"""
import pytest
from httpx import AsyncClient


class TestHealthCheck:
    """Test health check endpoint."""

    async def test_health_endpoint(self, client: AsyncClient):
        """Test that health endpoint returns correct response."""
        response = await client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "environment" in data


class TestAPIAuthentication:
    """Test API authentication."""

    async def test_protected_endpoint_without_auth(self, client: AsyncClient):
        """Test that protected endpoints require authentication."""
        response = await client.get("/api/v1/status/test-uuid")
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data

    async def test_protected_endpoint_with_invalid_auth(self, client: AsyncClient):
        """Test that invalid API key is rejected."""
        headers = {"Authorization": "Bearer invalid-api-key"}
        response = await client.get("/api/v1/status/test-uuid", headers=headers)
        assert response.status_code == 401


class TestAPIValidation:
    """Test API input validation."""

    async def test_invalid_uuid_format(self, client: AsyncClient):
        """Test that invalid UUID format is rejected."""
        headers = {"Authorization": "Bearer test-api-key-for-ci"}
        response = await client.get("/api/v1/status/invalid-uuid", headers=headers)
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
        assert "uuid_parsing" in str(data)


if __name__ == "__main__":
    pytest.main([__file__])
