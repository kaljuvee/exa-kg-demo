"""
Unit tests for Companies House API integration
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the utils directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from companies_house_api import CompaniesHouseAPI, CompanyProfile, Officer, PSC

class TestCompaniesHouseAPI(unittest.TestCase):
    """Test cases for Companies House API client"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key"
        self.api = CompaniesHouseAPI(self.api_key)
    
    def test_init(self):
        """Test API client initialization"""
        self.assertEqual(self.api.api_key, self.api_key)
        self.assertEqual(self.api.base_url, "https://api.company-information.service.gov.uk")
        self.assertEqual(self.api.session.auth, (self.api_key, ''))
    
    @patch('companies_house_api.requests.Session.get')
    def test_search_companies_success(self, mock_get):
        """Test successful company search"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [
                {
                    'company_number': '00000001',
                    'title': 'TEST COMPANY LIMITED',
                    'company_status': 'active',
                    'company_type': 'ltd'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test search
        results = self.api.search_companies("TEST COMPANY")
        
        # Assertions
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['company_number'], '00000001')
        self.assertEqual(results[0]['title'], 'TEST COMPANY LIMITED')
        
        # Verify API call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn('q', kwargs['params'])
        self.assertEqual(kwargs['params']['q'], 'TEST COMPANY')
    
    @patch('companies_house_api.requests.Session.get')
    def test_search_companies_no_results(self, mock_get):
        """Test company search with no results"""
        # Mock empty response
        mock_response = Mock()
        mock_response.json.return_value = {'items': []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test search
        results = self.api.search_companies("NONEXISTENT COMPANY")
        
        # Assertions
        self.assertEqual(len(results), 0)
    
    @patch('companies_house_api.requests.Session.get')
    def test_get_company_profile_success(self, mock_get):
        """Test successful company profile retrieval"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'company_number': '00000001',
            'company_name': 'TEST COMPANY LIMITED',
            'company_status': 'active',
            'date_of_creation': '2020-01-01',
            'type': 'ltd',
            'sic_codes': ['70100', '82990'],
            'registered_office_address': {
                'address_line_1': '123 Test Street',
                'locality': 'London',
                'postal_code': 'SW1A 1AA'
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test profile retrieval
        profile = self.api.get_company_profile('00000001')
        
        # Assertions
        self.assertIsInstance(profile, CompanyProfile)
        self.assertEqual(profile.company_number, '00000001')
        self.assertEqual(profile.company_name, 'TEST COMPANY LIMITED')
        self.assertEqual(profile.company_status, 'active')
        self.assertEqual(profile.sic_codes, ['70100', '82990'])
    
    @patch('companies_house_api.requests.Session.get')
    def test_get_officers_success(self, mock_get):
        """Test successful officers retrieval"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [
                {
                    'name': 'SMITH, John',
                    'officer_role': 'director',
                    'appointed_on': '2020-01-01',
                    'nationality': 'British',
                    'occupation': 'Director',
                    'country_of_residence': 'England',
                    'links': {
                        'officer': {
                            'appointments': '/officers/abc123/appointments'
                        }
                    }
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test officers retrieval
        officers = self.api.get_officers('00000001')
        
        # Assertions
        self.assertEqual(len(officers), 1)
        self.assertIsInstance(officers[0], Officer)
        self.assertEqual(officers[0].name, 'SMITH, John')
        self.assertEqual(officers[0].role, 'director')
        self.assertEqual(officers[0].nationality, 'British')
    
    @patch('companies_house_api.requests.Session.get')
    def test_get_pscs_success(self, mock_get):
        """Test successful PSCs retrieval"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [
                {
                    'name': 'Mr John Smith',
                    'kind': 'individual-person-with-significant-control',
                    'natures_of_control': ['ownership-of-shares-75-to-100-percent'],
                    'notified_on': '2020-01-01',
                    'country_of_residence': 'England',
                    'nationality': 'British',
                    'links': {
                        'self': '/company/00000001/persons-with-significant-control/individual/xyz789'
                    }
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test PSCs retrieval
        pscs = self.api.get_pscs('00000001')
        
        # Assertions
        self.assertEqual(len(pscs), 1)
        self.assertIsInstance(pscs[0], PSC)
        self.assertEqual(pscs[0].name, 'Mr John Smith')
        self.assertEqual(pscs[0].psc_type, 'individual')
        self.assertEqual(pscs[0].nature_of_control, ['ownership-of-shares-75-to-100-percent'])
    
    @patch.object(CompaniesHouseAPI, '_make_request')
    def test_api_error_handling(self, mock_make_request):
        """Test API error handling"""
        # Mock request to return None (simulating error)
        mock_make_request.return_value = None
        
        # Test that methods handle errors gracefully
        companies = self.api.search_companies("TEST")
        profile = self.api.get_company_profile("00000001")
        officers = self.api.get_officers("00000001")
        pscs = self.api.get_pscs("00000001")
        
        # Assertions
        self.assertEqual(companies, [])
        self.assertIsNone(profile)
        self.assertEqual(officers, [])
        self.assertEqual(pscs, [])
    
    @patch('companies_house_api.time.sleep')
    @patch('companies_house_api.time.time')
    def test_rate_limiting(self, mock_time, mock_sleep):
        """Test rate limiting functionality"""
        # Mock time to simulate rapid requests
        mock_time.side_effect = [0, 0.05, 0.1, 0.15]  # Simulate times
        
        # Test rate limiting
        self.api._rate_limit()
        self.api._rate_limit()
        
        # Verify sleep was called for rate limiting
        mock_sleep.assert_called()
    
    @patch.object(CompaniesHouseAPI, 'search_companies')
    @patch.object(CompaniesHouseAPI, 'get_company_profile')
    @patch.object(CompaniesHouseAPI, 'get_officers')
    @patch.object(CompaniesHouseAPI, 'get_pscs')
    def test_get_company_network(self, mock_pscs, mock_officers, mock_profile, mock_search):
        """Test company network building"""
        # Mock search results
        mock_search.return_value = [
            {'company_number': '00000001', 'title': 'TEST COMPANY LIMITED'}
        ]
        
        # Mock company profile
        mock_profile.return_value = CompanyProfile(
            company_number='00000001',
            company_name='TEST COMPANY LIMITED',
            company_status='active',
            incorporation_date='2020-01-01',
            company_type='ltd',
            sic_codes=['70100'],
            registered_address={},
            business_activity='Test business'
        )
        
        # Mock officers
        mock_officers.return_value = [
            Officer(
                officer_id='abc123',
                name='John Smith',
                role='director',
                appointed_on='2020-01-01',
                resigned_on=None,
                nationality='British',
                occupation='Director',
                country_of_residence='England'
            )
        ]
        
        # Mock PSCs
        mock_pscs.return_value = [
            PSC(
                psc_id='xyz789',
                name='Mr John Smith',
                psc_type='individual',
                nature_of_control=['ownership-of-shares-75-to-100-percent'],
                notified_on='2020-01-01',
                country_of_residence='England',
                nationality='British'
            )
        ]
        
        # Test network building
        network = self.api.get_company_network('TEST COMPANY')
        
        # Assertions
        self.assertIn('nodes', network)
        self.assertIn('edges', network)
        self.assertIn('metadata', network)
        
        # Check nodes
        nodes = network['nodes']
        company_nodes = [n for n in nodes if n['type'] == 'Company']
        person_nodes = [n for n in nodes if n['type'] == 'Person']
        psc_nodes = [n for n in nodes if n['type'] == 'PSC']
        
        self.assertEqual(len(company_nodes), 1)
        self.assertEqual(len(person_nodes), 1)
        self.assertEqual(len(psc_nodes), 1)
        
        # Check edges
        edges = network['edges']
        self.assertEqual(len(edges), 2)  # One for director, one for PSC

class TestDataClasses(unittest.TestCase):
    """Test data classes"""
    
    def test_company_profile_creation(self):
        """Test CompanyProfile data class"""
        profile = CompanyProfile(
            company_number='00000001',
            company_name='TEST COMPANY LIMITED',
            company_status='active',
            incorporation_date='2020-01-01',
            company_type='ltd',
            sic_codes=['70100'],
            registered_address={'address_line_1': '123 Test St'},
            business_activity='Testing'
        )
        
        self.assertEqual(profile.company_number, '00000001')
        self.assertEqual(profile.company_name, 'TEST COMPANY LIMITED')
        self.assertEqual(profile.sic_codes, ['70100'])
    
    def test_officer_creation(self):
        """Test Officer data class"""
        officer = Officer(
            officer_id='abc123',
            name='John Smith',
            role='director',
            appointed_on='2020-01-01',
            resigned_on=None,
            nationality='British',
            occupation='Director',
            country_of_residence='England'
        )
        
        self.assertEqual(officer.name, 'John Smith')
        self.assertEqual(officer.role, 'director')
        self.assertIsNone(officer.resigned_on)
    
    def test_psc_creation(self):
        """Test PSC data class"""
        psc = PSC(
            psc_id='xyz789',
            name='Mr John Smith',
            psc_type='individual',
            nature_of_control=['ownership-of-shares-75-to-100-percent'],
            notified_on='2020-01-01',
            country_of_residence='England',
            nationality='British'
        )
        
        self.assertEqual(psc.name, 'Mr John Smith')
        self.assertEqual(psc.psc_type, 'individual')
        self.assertEqual(len(psc.nature_of_control), 1)

if __name__ == '__main__':
    unittest.main()
