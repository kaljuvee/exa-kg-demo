import unittest
import json
import os
import sys
from unittest.mock import patch

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.companies_house_api import CompaniesHouseAPI

class TestCompaniesHouseAPIReal(unittest.TestCase):
    """Test CompaniesHouseAPI with real test data instead of mocks"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = CompaniesHouseAPI(api_key="test_key")
        self.test_data_dir = os.path.join(os.path.dirname(__file__), '..', 'test-data')
        
    def load_test_data(self, filename):
        """Load test data from JSON file"""
        filepath = os.path.join(self.test_data_dir, filename)
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def test_search_companies_with_real_data(self):
        """Test company search with real API response data"""
        # Load real test data
        test_data = self.load_test_data('companies_house_search_tesco.json')
        
        # Mock the API call to return our test data
        with patch.object(self.client, '_make_request') as mock_request:
            mock_request.return_value = test_data
            
            results = self.client.search_companies("Tesco")
            
            # Verify the results structure
            self.assertIsInstance(results, list)
            self.assertGreater(len(results), 0)
            
            # Check first result structure
            first_result = results[0]
            self.assertIn('company_number', first_result)
            self.assertIn('title', first_result)
            self.assertIn('company_status', first_result)
            self.assertEqual(first_result['company_number'], '00445790')
            self.assertEqual(first_result['title'], 'TESCO PLC')
            self.assertEqual(first_result['company_status'], 'active')
    
    def test_get_company_profile_with_real_data(self):
        """Test company profile retrieval with real API response data"""
        # Load real test data
        test_data = self.load_test_data('companies_house_profile_tesco.json')
        
        # Mock the API call to return our test data
        with patch.object(self.client, '_make_request') as mock_request:
            mock_request.return_value = test_data
            
            profile = self.client.get_company_profile("00445790")
            
            # Verify the profile structure
            self.assertIsNotNone(profile)
            self.assertEqual(profile['company_number'], '00445790')
            self.assertEqual(profile['company_name'], 'TESCO PLC')
            self.assertEqual(profile['company_status'], 'active')
            self.assertEqual(profile['company_type'], 'plc')
            self.assertEqual(profile['date_of_creation'], '1947-11-27')
            
            # Check SIC codes
            self.assertIn('sic_codes', profile)
            self.assertEqual(profile['sic_codes'], ['47110'])
            
            # Check registered office address
            self.assertIn('registered_office_address', profile)
            address = profile['registered_office_address']
            self.assertEqual(address['locality'], 'Welwyn Garden City')
            self.assertEqual(address['postal_code'], 'AL7 1GA')
    
    def test_get_company_officers_with_real_data(self):
        """Test company officers retrieval with real API response data"""
        # Load real test data
        test_data = self.load_test_data('companies_house_officers_tesco.json')
        
        # Mock the API call to return our test data
        with patch.object(self.client, '_make_request') as mock_request:
            mock_request.return_value = test_data
            
            officers = self.client.get_company_officers("00445790")
            
            # Verify the officers structure
            self.assertIsInstance(officers, list)
            self.assertEqual(len(officers), 4)
            
            # Check first officer (secretary)
            secretary = officers[0]
            self.assertEqual(secretary['name'], 'TAYLOR, Christopher Jon')
            self.assertEqual(secretary['officer_role'], 'secretary')
            self.assertEqual(secretary['appointed_on'], '2025-04-14')
            
            # Check director
            director = next(o for o in officers if o['name'] == 'BETHELL, Melissa')
            self.assertEqual(director['officer_role'], 'director')
            self.assertEqual(director['nationality'], 'British')
            self.assertEqual(director['occupation'], 'Company Director')
            
            # Check international director
            intl_director = next(o for o in officers if o['name'] == 'BODSON, Bertrand Jean Francois')
            self.assertEqual(intl_director['nationality'], 'Belgian')
            self.assertEqual(intl_director['country_of_residence'], 'Belgium')
    
    def test_get_company_pscs_with_real_data(self):
        """Test company PSCs retrieval with real API response data"""
        # Load real test data
        test_data = self.load_test_data('companies_house_pscs_tesco.json')
        
        # Mock the API call to return our test data
        with patch.object(self.client, '_make_request') as mock_request:
            mock_request.return_value = test_data
            
            pscs = self.client.get_company_pscs("00445790")
            
            # Verify the PSCs structure
            self.assertIsInstance(pscs, list)
            self.assertEqual(len(pscs), 2)
            
            # Check individual PSC
            individual_psc = next(p for p in pscs if p['kind'] == 'individual-person-with-significant-control')
            self.assertEqual(individual_psc['name'], 'Miss Susan Anderson')
            self.assertEqual(individual_psc['nationality'], 'British')
            self.assertIn('ownership-of-shares-25-to-50-percent', individual_psc['natures_of_control'])
            self.assertIn('voting-rights-25-to-50-percent', individual_psc['natures_of_control'])
            
            # Check corporate PSC
            corporate_psc = next(p for p in pscs if p['kind'] == 'corporate-entity-person-with-significant-control')
            self.assertEqual(corporate_psc['name'], 'TESCO PENSION TRUSTEES LIMITED')
            self.assertIn('identification', corporate_psc)
            self.assertEqual(corporate_psc['identification']['registration_number'], '02345678')
    
    def test_rate_limiting_behavior(self):
        """Test that rate limiting is properly handled"""
        # This test verifies that the client respects rate limits
        # In real usage, this would be handled by the _make_request method
        
        # Mock a rate limit response (429 status)
        with patch.object(self.client, '_make_request') as mock_request:
            mock_request.side_effect = Exception("429 Too Many Requests")
            
            result = self.client.search_companies("test")
            self.assertIsNone(result)
    
    def test_company_not_found_handling(self):
        """Test handling of company not found scenarios"""
        # Mock a 404 response
        with patch.object(self.client, '_make_request') as mock_request:
            mock_request.side_effect = Exception("404 Not Found")
            
            result = self.client.get_company_profile("99999999")
            self.assertIsNone(result)
    
    def test_data_validation(self):
        """Test that real test data has expected structure"""
        # Test search data structure
        search_data = self.load_test_data('companies_house_search_tesco.json')
        self.assertIn('items', search_data)
        self.assertIn('total_results', search_data)
        self.assertIn('query', search_data)
        
        # Test company profile structure
        profile_data = self.load_test_data('companies_house_profile_tesco.json')
        required_fields = ['company_number', 'company_name', 'company_status', 'company_type']
        for field in required_fields:
            self.assertIn(field, profile_data, f"Missing field: {field}")
        
        # Test officers data structure
        officers_data = self.load_test_data('companies_house_officers_tesco.json')
        self.assertIn('items', officers_data)
        self.assertIn('total_results', officers_data)
        
        for officer in officers_data['items']:
            required_fields = ['name', 'officer_role', 'appointed_on']
            for field in required_fields:
                self.assertIn(field, officer, f"Missing field: {field}")
        
        # Test PSCs data structure
        pscs_data = self.load_test_data('companies_house_pscs_tesco.json')
        self.assertIn('items', pscs_data)
        
        for psc in pscs_data['items']:
            required_fields = ['name', 'kind', 'natures_of_control']
            for field in required_fields:
                self.assertIn(field, psc, f"Missing field: {field}")
    
    def test_business_activity_mapping(self):
        """Test that SIC codes are properly mapped to business activities"""
        profile_data = self.load_test_data('companies_house_profile_tesco.json')
        
        # Mock the API call
        with patch.object(self.client, '_make_request') as mock_request:
            mock_request.return_value = profile_data
            
            profile = self.client.get_company_profile("00445790")
            
            # Verify SIC code is present
            self.assertIn('sic_codes', profile)
            self.assertEqual(profile['sic_codes'], ['47110'])
            
            # In a real implementation, we might map SIC codes to descriptions
            # SIC 47110 = "Retail sale in non-specialised stores with food, beverages or tobacco predominating"

if __name__ == '__main__':
    unittest.main()
