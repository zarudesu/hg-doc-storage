"""
Tests for the configuration and application setup
"""
import pytest
from app.core.config import Settings


class TestConfiguration:
    """Test application configuration."""

    def test_settings_creation(self):
        """Test that settings can be created."""
        settings = Settings()
        assert settings is not None
        assert settings.app_name is not None
        assert settings.environment is not None

    def test_default_values(self):
        """Test that default configuration values are set."""
        settings = Settings()
        assert settings.max_file_size > 0
        assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]
        assert settings.minio_endpoint is not None


class TestImports:
    """Test that all modules can be imported."""

    def test_app_imports(self):
        """Test that main app modules import correctly."""
        from app.main import app
        from app.core.config import settings
        from app.api.v1 import upload, download, status
        
        assert app is not None
        assert settings is not None

    def test_model_imports(self):
        """Test that database models import correctly."""
        from app.models.contract import Contract
        assert Contract is not None


if __name__ == "__main__":
    pytest.main([__file__])
