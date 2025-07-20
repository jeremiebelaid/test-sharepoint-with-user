"""
Tests pour l'authentification SharePoint
"""
import pytest
import os
from unittest.mock import Mock, patch
from sharepoint_auth import SharePointAuthenticator

class TestSharePointAuthenticator:
    """Tests pour la classe SharePointAuthenticator"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.site_url = "https://test.sharepoint.com/sites/test"
        self.authenticator = SharePointAuthenticator(self.site_url)
    
    @patch('sharepoint_auth.ManagedIdentityCredential')
    def test_authenticate_success(self, mock_credential):
        """Test d'authentification réussie"""
        # Mock du credential
        mock_credential_instance = Mock()
        mock_credential_instance.get_token.return_value = Mock(expires_on=3600)
        mock_credential.return_value = mock_credential_instance
        
        # Mock du contexte SharePoint
        with patch('sharepoint_auth.ClientContext') as mock_context:
            mock_ctx = Mock()
            mock_web = Mock()
            mock_web.title = "Test Site"
            mock_ctx.web = mock_web
            mock_context.return_value.with_credentials.return_value = mock_ctx
            
            # Test
            result = self.authenticator.authenticate()
            
            assert result is True
            assert self.authenticator.ctx is not None
    
    @patch('sharepoint_auth.ManagedIdentityCredential')
    def test_authenticate_failure(self, mock_credential):
        """Test d'authentification échouée"""
        # Mock du credential qui lève une exception
        mock_credential.side_effect = Exception("Authentication failed")
        
        # Test
        result = self.authenticator.authenticate()
        
        assert result is False
        assert self.authenticator.ctx is None
    
    def test_get_site_info_not_authenticated(self):
        """Test de récupération d'infos sans authentification"""
        result = self.authenticator.get_site_info()
        assert result is None
    
    def test_list_lists_not_authenticated(self):
        """Test de liste des listes sans authentification"""
        result = self.authenticator.list_lists()
        assert result is None

def test_display_functions():
    """Test des fonctions d'affichage"""
    from sharepoint_auth import display_site_info, display_lists
    
    # Test display_site_info
    site_info = {"title": "Test", "url": "https://test.com"}
    # Cette fonction ne retourne rien, on teste juste qu'elle ne lève pas d'exception
    display_site_info(site_info)
    
    # Test display_lists
    lists_info = [{"title": "List1", "id": "123", "item_count": 5, "hidden": False}]
    display_lists(lists_info)

if __name__ == "__main__":
    pytest.main([__file__]) 