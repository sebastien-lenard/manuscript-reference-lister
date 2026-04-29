import unittest
from unittest.mock import patch, MagicMock
from style_fetcher import StyleFetcher

class TestStyleFetcher(unittest.TestCase):

    @patch('style_fetcher.time.sleep', return_value=None)
    @patch('style_fetcher.requests.get')
    def test_check_style_is_valid_success(self, mock_get, mock_sleep):
        # Mocking a successful API response with a list of styles
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': {
                'items': ['apa', 'harvard3', 'ieee', 'nature']
            }
        }
        mock_get.return_value = mock_response

        # Test with a valid style
        fetcher = StyleFetcher("apa")
        fetcher.check_style_is_valid()
        
        self.assertTrue(fetcher.style_is_valid)
        self.assertEqual(mock_get.call_count, 1)

    @patch('style_fetcher.time.sleep', return_value=None)
    @patch('style_fetcher.requests.get')
    def test_check_style_is_valid_failure(self, mock_get, mock_sleep):
        # Mocking a response where the style is missing
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': {
                'items': ['apa', 'ieee']
            }
        }
        mock_get.return_value = mock_response

        # Test with an invalid style
        fetcher = StyleFetcher("not-a-real-style")
        fetcher.check_style_is_valid()
        
        self.assertFalse(fetcher.style_is_valid)

if __name__ == '__main__':
    unittest.main()
