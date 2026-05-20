"""
Service Layer Tests
Tests for refactored business logic services
"""

import pytest
from datetime import datetime, timezone, timedelta
from services import (
    auth_service,
    partner_share_service,
    chemistry_service
)


class TestAuthService:
    """Tests for authentication service"""
    
    def test_generate_otp(self):
        """Test OTP generation"""
        code = auth_service.generate_otp()
        
        assert len(code) == 6
        assert code.isdigit()
        assert 0 <= int(code) <= 999999
    
    def test_normalize_email(self):
        """Test email normalization"""
        assert auth_service.normalize_email('Test@Example.COM  ') == 'test@example.com'
        assert auth_service.normalize_email('user@domain.org') == 'user@domain.org'
    
    def test_determine_role(self):
        """Test role determination"""
        # Mock admin email
        import os
        original = os.environ.get('ADMIN_EMAILS', '')
        os.environ['ADMIN_EMAILS'] = 'admin@test.com'
        
        # Reload module to pick up new env
        from importlib import reload
        import services.auth_service
        reload(services.auth_service)
        
        assert services.auth_service.determine_role('admin@test.com') == 'admin'
        assert services.auth_service.determine_role('user@test.com') == 'researcher'
        
        # Restore
        os.environ['ADMIN_EMAILS'] = original
        reload(services.auth_service)
    
    @pytest.mark.asyncio
    async def test_create_magic_code(self):
        """Test magic code creation"""
        result = await auth_service.create_magic_code('test@example.com')
        
        assert 'expires_at' in result
        assert isinstance(result['expires_at'], datetime)
        # In demo mode, code should be present
        if result.get('code'):
            assert len(result['code']) == 6


class TestPartnerShareService:
    """Tests for partner share service"""
    
    def test_generate_share_token(self):
        """Test share token generation"""
        share_id = 'test-share-123'
        file_id = 'file-456'
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        token = partner_share_service.generate_share_token(share_id, file_id, expires_at)
        
        # Token should have 4 parts separated by |
        parts = token.split('|')
        assert len(parts) == 4
        assert parts[0] == share_id
        assert parts[1] == file_id
        assert parts[2] == str(int(expires_at.timestamp()))
        # Part 3 is signature (64 char hex for SHA256)
        assert len(parts[3]) == 64
    
    def test_verify_share_token_valid(self):
        """Test share token verification with valid token"""
        share_id = 'test-share-123'
        file_id = 'file-456'
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Generate token
        token = partner_share_service.generate_share_token(share_id, file_id, expires_at)
        
        # Verify token
        result = partner_share_service.verify_share_token(token)
        
        assert result is not None
        assert result['share_id'] == share_id
        assert result['file_id'] == file_id
        # Allow 1 second tolerance for timestamp comparison
        assert abs((result['expires_at'] - expires_at).total_seconds()) < 1
    
    def test_verify_share_token_expired(self):
        """Test share token verification with expired token"""
        share_id = 'test-share-123'
        file_id = 'file-456'
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
        
        # Generate token
        token = partner_share_service.generate_share_token(share_id, file_id, expires_at)
        
        # Verify token should fail
        result = partner_share_service.verify_share_token(token)
        assert result is None
    
    def test_verify_share_token_invalid_signature(self):
        """Test share token verification with tampered token"""
        share_id = 'test-share-123'
        file_id = 'file-456'
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Generate valid token
        token = partner_share_service.generate_share_token(share_id, file_id, expires_at)
        
        # Tamper with token
        parts = token.split('|')
        parts[1] = 'tampered-file-id'
        tampered_token = '|'.join(parts)
        
        # Verification should fail
        result = partner_share_service.verify_share_token(tampered_token)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_share_access(self):
        """Test share access validation"""
        # Valid share
        share = {
            'share_id': 'test-123',
            'status': 'active',
            'expires_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            'download_count': 5,
            'policy': {
                'max_downloads': 10,
                'allowed_ips': []
            }
        }
        
        result = await partner_share_service.validate_share_access(share)
        assert result['allowed'] is True
        
        # Expired share
        share['expires_at'] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        result = await partner_share_service.validate_share_access(share)
        assert result['allowed'] is False
        assert 'expired' in result['reason'].lower()
        
        # Download limit reached
        share['expires_at'] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        share['download_count'] = 10
        result = await partner_share_service.validate_share_access(share)
        assert result['allowed'] is False
        assert 'limit' in result['reason'].lower()


class TestChemistryService:
    """Tests for chemistry service"""
    
    def test_get_chemistry_options_basic(self):
        """Test chemistry options for basic tier"""
        result = chemistry_service.get_chemistry_options('basic')
        
        assert 'tier' in result
        assert 'mods' in result
        assert 'exclusions' in result
        assert result['tier'] == 'basic'
        assert isinstance(result['mods'], list)
        assert isinstance(result['exclusions'], list)
    
    def test_get_chemistry_options_tiers(self):
        """Test tier filtering"""
        basic = chemistry_service.get_chemistry_options('basic')
        pro = chemistry_service.get_chemistry_options('pro')
        enterprise = chemistry_service.get_chemistry_options('enterprise')
        
        # Higher tiers should have at least as many options as lower tiers
        assert len(pro['mods']) >= len(basic['mods'])
        assert len(enterprise['mods']) >= len(pro['mods'])
    
    def test_tier_allows_access(self):
        """Test tier access control"""
        # Basic can access basic
        assert chemistry_service._tier_allows_access('basic', 'basic') is True
        
        # Basic cannot access pro
        assert chemistry_service._tier_allows_access('basic', 'pro') is False
        
        # Pro can access basic
        assert chemistry_service._tier_allows_access('pro', 'basic') is True
        
        # Enterprise can access all
        assert chemistry_service._tier_allows_access('enterprise', 'basic') is True
        assert chemistry_service._tier_allows_access('enterprise', 'pro') is True
        assert chemistry_service._tier_allows_access('enterprise', 'enterprise') is True


# Integration tests (require database)
class TestServiceIntegration:
    """Integration tests for services with database"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_auth_flow_end_to_end(self):
        """Test complete auth flow"""
        email = 'test@example.com'
        
        # Create magic code
        result = await auth_service.create_magic_code(email)
        assert 'expires_at' in result
        
        # Get code (in demo mode)
        if result.get('code'):
            code = result['code']
            
            # Verify code
            user_data = await auth_service.verify_magic_code(email, code)
            assert user_data is not None
            assert user_data['email'] == email.lower()
            
            # Verify same code again should fail (one-time use)
            user_data_2 = await auth_service.verify_magic_code(email, code)
            assert user_data_2 is None
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_partner_share_crud(self):
        """Test partner share CRUD operations"""
        # Create share
        share = await partner_share_service.create_partner_share(
            reclaim_pack_id='pack-123',
            recipient_org='Test Corp',
            recipient_email='partner@test.com',
            created_by='admin@test.com'
        )
        
        assert 'share_id' in share
        assert 'token' in share
        
        # Get share
        share_id = share['share_id']
        retrieved = await partner_share_service.get_share_by_id(share_id)
        assert retrieved is not None
        assert retrieved['share_id'] == share_id
        
        # Revoke share
        revoked = await partner_share_service.revoke_share(share_id)
        assert revoked is True
        
        # Check status
        retrieved_after = await partner_share_service.get_share_by_id(share_id)
        assert retrieved_after['status'] == 'revoked'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
