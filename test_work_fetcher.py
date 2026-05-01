import unittest
from unittest.mock import patch, MagicMock
from work_fetcher import WorkFetcher

class TestWorkFetcher(unittest.TestCase):
    def setUp(self):
        """Initialize the fetcher for each test."""
        self.fetcher = WorkFetcher()

    @patch('journal_fetcher.RequestsWrapper.get')
    def test_fetch_not_found(self, mock_wrapper_get):
        """Checks behavior when no results are found (should return empty list)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'message': {'items': []}}
        mock_wrapper_get.return_value = mock_response

        result = self.fetcher.fetch_dois_for_this_info("UnknownAuthor", "2025",
                                                       issn="1752-0894")
        self.assertEqual(result, [])

    @patch('journal_fetcher.RequestsWrapper.get')
    def test_returns_multiple_candidates(self, mock_wrapper_get):
        """Verifies that the fetcher returns multiple candidates."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': {
                'items': [
                    {'DOI': '10.1038/s41561-020-0585-2',
                     'type': 'journal-article',
                     'author': [{'family': 'Lenard', 'sequence': 'first'}]},
                    {'DOI': '10.1/ref2', 'type': 'proceedings-article',
                     'author': [{'family': 'Lenard', 'sequence': 'first'}]}
                ]
            }
        }
        mock_wrapper_get.return_value = mock_response
        self.fetcher._get_formatted_full_reference = MagicMock(return_value="APA String")

        results = self.fetcher.fetch_dois_for_this_info("Lenard et al.", "2020",
                                                        issn="1752-0894")
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['type'], "journal-article")
        self.assertEqual(results[0]['doi'], "https://doi.org/10.1038/s41561-020-0585-2")
        self.assertEqual(results[1]['type'], "proceedings-article")

    @patch('journal_fetcher.RequestsWrapper.get')
    def test_parameterized_keywords(self, mock_wrapper_get):
        """Verifies that custom keywords passed to the method are used in the query."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'message': {'items': []}}
        mock_wrapper_get.return_value = mock_response

        custom_kws = ("Shifts in landslide frequency–area distribution after forest "
                      "conversion in the tropical Andes")
        self.fetcher.fetch_dois_for_this_info("Guns and Vanacker", "2014",
                                              issn="2213-3054", keywords=custom_kws)
        
        # Check that the request URL contains our custom keywords
        _, kwargs = mock_wrapper_get.call_args
        params = kwargs.get('params', {})
        self.assertIn(custom_kws, params.get('query', ''))
    
    @patch('work_fetcher.RequestsWrapper.get')
    def test_author_validation_filtering(self, mock_wrapper_get):
        """
        Tests that items with non-matching first authors are filtered out.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': {
                'items': [
                    # Match: Correct family name
                    {'DOI': '10.1/match', 'author': [{'family': 'Guns', 'sequence': 'first'}]},
                    # No Match: Different family name
                    {'DOI': '10.1/wrong', 'author': [{'family': 'Smith', 'sequence': 'first'}]},
                    # Match: Metadata inverted (target in given name)
                    {'DOI': '10.1/inverted', 'author': [{'given': 'Guns', 'family': 'M.', 'sequence': 'first'}]}
                ]
            }
        }
        mock_wrapper_get.return_value = mock_response

        # We search for "Guns et al." -> clean_author becomes "Guns"
        results = self.fetcher.fetch_dois_for_this_info("Guns et al.", "2014", issn="2213-3054")
        
        # Should only keep 2 out of 3 candidates
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['doi'], "https://doi.org/10.1/match")
        self.assertEqual(results[1]['doi'], "https://doi.org/10.1/inverted")

    def test_validate_first_author_logic(self):
        """
        Directly tests the private _validate_first_author helper with various scenarios.
        """
        # Scenario A: Standard family name match
        item_a = {'author': [{'family': 'Lenard', 'sequence': 'first'}]}
        self.assertTrue(self.fetcher._validate_first_author(item_a, ["Lenard"]))

        # Scenario B: Matching using the 'name' key fallback (when 'family' is missing)
        item_b = {'author': [{'name': 'Lenard', 'sequence': 'first'}]}
        self.assertTrue(self.fetcher._validate_first_author(item_b, ["Lenard"]))

        # Scenario C: No 'sequence' key, should fallback to first list element
        item_c = {'author': [{'family': 'Lenard'}, {'family': 'Other'}]}
        self.assertTrue(self.fetcher._validate_first_author(item_c, ["Lenard"]))

        # Scenario D: Case insensitivity and whitespace
        item_d = {'author': [{'family': 'Van Dijk', 'sequence': 'first'}]}
        self.assertTrue(self.fetcher._validate_first_author(item_d, ["  van dijk  "]))

        # Scenario E: Total mismatch
        item_e = {'author': [{'family': 'Zappa', 'sequence': 'first'}]}
        self.assertFalse(self.fetcher._validate_first_author(item_e, ["Hendrix"]))

        # Scenario F: Accents and Cedillas (French)
        item_f = {'author': [{'family': 'Lénárd', 'sequence': 'first'}]}
        self.assertTrue(self.fetcher._validate_first_author(item_f, ["Lenard"]))
        
        item_f2 = {'author': [{'family': 'François', 'sequence': 'first'}]}
        self.assertTrue(self.fetcher._validate_first_author(item_f2, ["Francois"]))

        # Scenario G: Polish and Spanish characters
        # 'Ł' (L with stroke) and 'ñ' (n with tilde)
        item_g = {'author': [{'family': 'Łukasiewicz', 'sequence': 'first'}]}
        self.assertTrue(self.fetcher._validate_first_author(item_g, ["Lukasiewicz"]))
        
        item_g2 = {'author': [{'family': 'Peña', 'sequence': 'first'}]}
        self.assertTrue(self.fetcher._validate_first_author(item_g2, ["Pena"]))

        # Scenario H: Hungarian characters
        # 'ő' (o with double acute accent)
        item_h = {'author': [{'family': 'Erdős', 'sequence': 'first'}]}
        self.assertTrue(self.fetcher._validate_first_author(item_h, ["Erdos"]))

    def test_validate_author_counts_and_sequence(self):
        """
        Tests strict author count and second author validation.
        """
        # Scenario I: Single author expected (Lenard, 2020)
        # Match
        item_i1 = {'author': [{'family': 'Lenard', 'sequence': 'first'}]}
        self.assertTrue(self.fetcher._validate_first_author(item_i1, ["lenard"], 1))
        # Fail: Two authors found but only one expected
        item_i2 = {'author': [{'family': 'Lenard', 'sequence': 'first'}, {'family': 'Smith'}]}
        self.assertFalse(self.fetcher._validate_first_author(item_i2, ["lenard"], 1))

        # Scenario J: Two authors expected (Guns and Vanacker, 2014)
        # Match
        item_j1 = {'author': [
            {'family': 'Guns', 'sequence': 'first'},
            {'family': 'Vanacker', 'sequence': 'additional'}
        ]}
        self.assertTrue(self.fetcher._validate_first_author(item_j1, ["guns", "vanacker"], 2))
        # Fail: Second author name mismatch
        item_j2 = {'author': [
            {'family': 'Guns', 'sequence': 'first'},
            {'family': 'Dupont', 'sequence': 'additional'}
        ]}
        self.assertFalse(self.fetcher._validate_first_author(item_j2, ["guns", "vanacker"], 2))
        # Fail: Three authors found but only two expected
        item_j3 = {'author': [
            {'family': 'Guns', 'sequence': 'first'},
            {'family': 'Vanacker'},
            {'family': 'Third'}
        ]}
        self.assertFalse(self.fetcher._validate_first_author(item_j3, ["guns", "vanacker"], 2))

        # Scenario K: "et al." case (No upper limit)
        item_k = {'author': [{'family': 'Lenard', 'sequence': 'first'}, {'family': 'A'}, {'family': 'B'}]}
        # expected_count is None for et al.
        self.assertTrue(self.fetcher._validate_first_author(item_k, ["lenard"], None))

if __name__ == '__main__':
    unittest.main()