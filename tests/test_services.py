import pytest
from unittest.mock import AsyncMock, patch
from app.services.contract_service import ContractService
from app.core.schemas import ContractInitiate, ContractSign
import uuid


class TestContractService:
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        mock = AsyncMock()
        return mock
    
    @pytest.fixture
    def sample_contract_data(self):
        """Sample contract data for testing"""
        return ContractInitiate(
            client_id="test_client_001",
            type="surgery"
        )
    
    @pytest.fixture
    def sample_sign_data(self):
        """Sample signing data for testing"""
        return ContractSign(
            signer_id="admin_001",
            signature_hash="abc123def456"
        )
    
    @patch('app.services.contract_service.minio_service')
    async def test_create_contract(self, mock_minio, mock_db, sample_contract_data):
        """Test contract creation"""
        # Setup mocks
        mock_minio.upload_file = AsyncMock()
        
        # Test data
        pdf_content = b"fake pdf content"
        client_ip = "127.0.0.1"
        
        # Call service method
        contract = await ContractService.create_contract(
            mock_db, sample_contract_data, pdf_content, client_ip
        )
        
        # Verify minio upload was called
        mock_minio.upload_file.assert_called_once()
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        mock_db.refresh.assert_called_once()
    
    async def test_get_contract(self, mock_db):
        """Test getting contract by ID"""
        # Setup mock
        test_uuid = uuid.uuid4()
        mock_db.execute = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = "mock_contract"
        mock_db.execute.return_value = mock_result
        
        # Call service method
        result = await ContractService.get_contract(mock_db, test_uuid)
        
        # Verify
        assert result == "mock_contract"
        mock_db.execute.assert_called_once()
    
    @patch('app.services.contract_service.minio_service')
    async def test_sign_contract(self, mock_minio, mock_db, sample_sign_data):
        """Test contract signing"""
        # Setup mocks
        test_uuid = uuid.uuid4()
        mock_contract = AsyncMock()
        mock_contract.status = "new"
        
        mock_minio.upload_file = AsyncMock()
        
        with patch.object(ContractService, 'get_contract', return_value=mock_contract):
            # Test data
            pdf_content = b"signed pdf content"
            client_ip = "127.0.0.1"
            
            # Call service method
            result = await ContractService.sign_contract(
                mock_db, test_uuid, pdf_content, sample_sign_data, client_ip
            )
            
            # Verify minio upload was called
            mock_minio.upload_file.assert_called_once()
            
            # Verify database update
            mock_db.execute.assert_called()
            mock_db.commit.assert_called()
    
    async def test_sign_already_signed_contract(self, mock_db, sample_sign_data):
        """Test signing already signed contract"""
        # Setup mock
        test_uuid = uuid.uuid4()
        mock_contract = AsyncMock()
        mock_contract.status = "signed"  # Already signed
        
        with patch.object(ContractService, 'get_contract', return_value=mock_contract):
            pdf_content = b"signed pdf content"
            client_ip = "127.0.0.1"
            
            # Should raise ValueError
            with pytest.raises(ValueError, match="already signed"):
                await ContractService.sign_contract(
                    mock_db, test_uuid, pdf_content, sample_sign_data, client_ip
                )
    
    async def test_log_access(self, mock_db):
        """Test access logging"""
        test_uuid = uuid.uuid4()
        
        await ContractService.log_access(
            mock_db, test_uuid, "127.0.0.1", "test_event"
        )
        
        # Verify log was added to database
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
