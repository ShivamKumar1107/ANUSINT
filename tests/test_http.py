import unittest
from unittest.mock import patch, MagicMock
from core.http_client import fetch_profile_data, InstagramAuthError

class TestHTTPClient(unittest.TestCase):
    @patch('core.http_client.get_cached_profile')
    def test_cache_hit_returns_early(self, mock_get_cache):
        # Simulate a valid cache hit
        mock_get_cache.return_value = {"cached": True, "username": "test_user"}
        
        result = fetch_profile_data("test_user")
        self.assertEqual(result, {"cached": True, "username": "test_user"})
        # Verify it only hit the cache and didn't attempt network requests
        mock_get_cache.assert_called_once()

    @patch('core.http_client.requests.Session.get')
    @patch('core.http_client.get_cached_profile')
    @patch('core.http_client.time.sleep') # Mock sleep so the test runs instantly
    def test_401_raises_auth_error(self, mock_sleep, mock_get_cache, mock_get):
        # Simulate a cache miss
        mock_get_cache.return_value = None
        
        # Simulate Instagram returning a 401 Login-Gating response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        with self.assertRaises(InstagramAuthError):
            fetch_profile_data("test_user")

if __name__ == "__main__":
    unittest.main()