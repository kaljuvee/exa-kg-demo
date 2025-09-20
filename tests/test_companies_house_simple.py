import unittest
import json
import os
import sys
from unittest.mock import patch

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.companies_house_api import CompaniesHouseAPI, CompanyProfile, Officer, PSC

class TestCompaniesHouseAPISimple(unittest.TestCase):
    """Test CompaniesHouseAPI with real test data - simplified version"""
    
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
            self.assertIsInstance(profile, CompanyProfile)
            self.assertEqual(profile.company_number, '00445790')
            self.assertEqual(profile.company_name, 'TESCO PLC')
            self.assertEqual(profile.company_status, 'active')
            # The API returns 'type' field, but our test data might not have it
            # Let's check what we actually get
            self.assertIsNotNone(profile.company_type)
            self.assertEqual(profile.incorporation_date, '1947-11-27')
            
            # Check SIC codes
            self.assertEqual(profile.sic_codes, ['47110'])
            
            # Check registered office address
            self.assertIsInstance(profile.registered_address, dict)
            self.assertEqual(profile.registered_address['locality'], 'Welwyn Garden City')
            self.assertEqual(profile.registered_address['postal_code'], 'AL7 1GA')
    
    def test_get_officers_with_real_data(self):
        """Test company officers retrieval with real API response data"""
        # Load real test data
        test_data = self.load_test_data('companies_house_officers_tesco.json')
        
        # Mock the API call to return our test data
        with patch.object(self.client, '_make_request') as mock_request:
            mock_request.return_value = test_data
            
            officers = self.client.get_officers("00445790")
            
            # Verify the officers structure
            self.assertIsInstance(officers, list)
            self.assertEqual(len(officers), 4)
            
            # Check first officer (secretary)
            secretary = officers[0]
            self.assertIsInstance(secretary, Officer)
            self.assertEqual(secretary.name, 'TAYLOR, Christopher Jon')
            self.assertEqual(secretary.role, 'secretary')
            self.assertEqual(secretary.appointed_on, '2025-04-14')
            
            # Check director
            director = next(o for o in officers if o.name == 'BETHELL, Melissa')
            self.assertEqual(director.role, 'director')
            self.assertEqual(director.nationality, 'British')
            self.assertEqual(director.occupation, 'Company Director')
            
            # Check international director
            intl_director = next(o for o in officers if o.name == 'BODSON, Bertrand Jean Francois')
            self.assertEqual(intl_director.nationality, 'Belgian')
            self.assertEqual(intl_director.country_of_residence, 'Belgium')
    
    def test_get_pscs_with_real_data(self):
        """Test company PSCs retrieval with real API response data"""
        # Load real test data
        test_data = self.load_test_data('companies_house_pscs_tesco.json')
        
        # Mock the API call to return our test data
        with patch.object(self.client, '_make_request') as mock_request:
            mock_request.return_value = test_data
            
            pscs = self.client.get_pscs("00445790")
            
            # Verify the PSCs structure
            self.assertIsInstance(pscs, list)
            self.assertEqual(len(pscs), 2)
            
            # Check individual PSC
            individual_psc = next(p for p in pscs if p.psc_type == 'individual')
            self.assertIsInstance(individual_psc, PSC)
            self.assertEqual(individual_psc.name, 'Miss Susan Anderson')
            self.assertEqual(individual_psc.nationality, 'British')
            self.assertIn('ownership-of-shares-25-to-50-percent', individual_psc.nature_of_control)
            self.assertIn('voting-rights-25-to-50-percent', individual_psc.nature_of_control)
            
            # Check corporate PSC
            corporate_psc = next(p for p in pscs if p.psc_type == 'corporate-entity')
            self.assertEqual(corporate_psc.name, 'TESCO PENSION TRUSTEES LIMITED')
    
    def test_error_handling_with_none_response(self):
        """Test error handling when API returns None"""
        # Mock a None response
        with patch.object(self.client, '_make_request') as mock_request:
            mock_request.return_value = None
            
            result = self.client.search_companies("test")
            self.assertEqual(result, [])
            
            profile = self.client.get_company_profile("99999999")
            self.assertIsNone(profile)
            
            officers = self.client.get_officers("99999999")
            self.assertEqual(officers, [])
            
            pscs = self.client.get_pscs("99999999")
            self.assertEqual(pscs, [])
    
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
    
    def test_dataclass_creation(self):
        """Test that dataclasses are created correctly"""
        # Test CompanyProfile creation
        profile = CompanyProfile(
            company_number="00445790",
            company_name="TESCO PLC",
            company_status="active",
            incorporation_date="1947-11-27",
            company_type="plc",
            sic_codes=["47110"],
            registered_address={"locality": "Welwyn Garden City"},
            business_activity="Retail"
        )
        
        self.assertEqual(profile.company_number, "00445790")
        self.assertEqual(profile.company_name, "TESCO PLC")
        self.assertEqual(profile.sic_codes, ["47110"])
        
        # Test Officer creation
        officer = Officer(
            officer_id="abc123",
            name="John Smith",
            role="director",
            appointed_on="2020-01-01",
            resigned_on=None,
            nationality="British",
            occupation="Director",
            country_of_residence="England"
        )
        
        self.assertEqual(officer.name, "John Smith")
        self.assertEqual(officer.role, "director")
        self.assertEqual(officer.nationality, "British")
        
        # Test PSC creation
        psc = PSC(
            psc_id="psc123",
            name="Jane Doe",
            psc_type="individual",
            nature_of_control=["ownership-of-shares-25-to-50-percent"],
            notified_on="2016-04-06",
            country_of_residence="England",
            nationality="British"
        )
        
        self.assertEqual(psc.name, "Jane Doe")
        self.assertEqual(psc.psc_type, "individual")
        self.assertIn("ownership-of-shares-25-to-50-percent", psc.nature_of_control)

if __name__ == '__main__':
    unittest.main()
