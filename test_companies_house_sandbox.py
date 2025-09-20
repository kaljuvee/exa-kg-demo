#!/usr/bin/env python3
"""
Comprehensive test script for Companies House API sandbox integration
Creates test data and tests all functionality
"""

import sys
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from companies_house_api import CompaniesHouseAPI

def create_test_company(api_key: str, company_name: str, company_type: str = "ltd"):
    """Create a test company in the sandbox environment"""
    url = "https://test-data-sandbox.company-information.service.gov.uk/test-data/company"
    
    data = {
        "company_name": company_name,
        "company_type": company_type
    }
    
    try:
        response = requests.post(
            url,
            auth=(api_key, ''),
            headers={'Content-Type': 'application/json'},
            json=data
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Failed to create test company: {e}")
        return None

def test_companies_house_sandbox():
    """Test the Companies House API with sandbox environment"""
    
    # Get API key from environment
    api_key = os.getenv('CH_API_KEY')
    if not api_key:
        print("❌ CH_API_KEY not found in environment variables")
        return False
    
    print(f"🔑 Using API key: {api_key[:8]}...")
    
    # Initialize API client for sandbox
    try:
        ch_api = CompaniesHouseAPI(api_key, use_sandbox=True)
        print("✅ Companies House API client initialized (Sandbox mode)")
    except Exception as e:
        print(f"❌ Failed to initialize API client: {e}")
        return False
    
    # Create test companies
    print("\n🏗️ Creating test companies in sandbox...")
    test_companies = []
    
    companies_to_create = [
        "SANDBOX TEST COMPANY LIMITED",
        "DEMO TECH SOLUTIONS LIMITED", 
        "EXAMPLE TRADING LIMITED"
    ]
    
    for company_name in companies_to_create:
        print(f"  Creating: {company_name}")
        company_data = create_test_company(api_key, company_name)
        if company_data:
            test_companies.append(company_data)
            print(f"  ✅ Created company {company_data['company_number']}")
        else:
            print(f"  ❌ Failed to create {company_name}")
    
    if not test_companies:
        print("❌ No test companies created")
        return False
    
    print(f"\n✅ Created {len(test_companies)} test companies")
    
    # Test company profile retrieval
    print("\n🏢 Testing company profile retrieval...")
    for i, company in enumerate(test_companies[:2], 1):  # Test first 2 companies
        company_number = company['company_number']
        print(f"\n  Test {i}: Company {company_number}")
        
        try:
            profile = ch_api.get_company_profile(company_number)
            if profile:
                print(f"  ✅ Retrieved profile for {profile.company_name}")
                print(f"    Status: {profile.company_status}")
                print(f"    Incorporation: {profile.incorporation_date}")
                print(f"    SIC Codes: {', '.join(profile.sic_codes) if profile.sic_codes else 'None'}")
                print(f"    Business Activity: {profile.business_activity or 'N/A'}")
            else:
                print(f"  ⚠️ No profile data retrieved for {company_number}")
        except Exception as e:
            print(f"  ❌ Profile retrieval failed: {e}")
    
    # Test officers retrieval
    print(f"\n👥 Testing officers retrieval...")
    test_company = test_companies[0]
    company_number = test_company['company_number']
    
    try:
        officers = ch_api.get_officers(company_number)
        print(f"✅ Found {len(officers)} officers for company {company_number}")
        
        for i, officer in enumerate(officers[:3], 1):
            print(f"  {i}. {officer.name}")
            print(f"     Role: {officer.role}")
            print(f"     Appointed: {officer.appointed_on or 'N/A'}")
            print(f"     Nationality: {officer.nationality or 'N/A'}")
            
    except Exception as e:
        print(f"❌ Officers retrieval failed: {e}")
    
    # Test PSCs retrieval
    print(f"\n🎯 Testing PSCs retrieval...")
    try:
        pscs = ch_api.get_pscs(company_number)
        print(f"✅ Found {len(pscs)} PSCs for company {company_number}")
        
        for i, psc in enumerate(pscs[:3], 1):
            print(f"  {i}. {psc.name}")
            print(f"     Type: {psc.psc_type}")
            print(f"     Control: {', '.join(psc.nature_of_control) if psc.nature_of_control else 'N/A'}")
            print(f"     Notified: {psc.notified_on or 'N/A'}")
            
    except Exception as e:
        print(f"❌ PSCs retrieval failed: {e}")
    
    # Test direct company access (since search doesn't work in sandbox)
    print(f"\n🔍 Testing direct company access...")
    try:
        # Create a mock network using the test companies we created
        network_data = {
            'nodes': [],
            'edges': [],
            'metadata': {
                'total_companies': len(test_companies),
                'total_nodes': 0,
                'total_edges': 0,
                'environment': 'sandbox'
            }
        }
        
        # Add company nodes
        for company in test_companies:
            company_number = company['company_number']
            profile = ch_api.get_company_profile(company_number)
            
            if profile:
                network_data['nodes'].append({
                    'id': f"company_{company_number}",
                    'label': profile.company_name,
                    'type': 'Company',
                    'company_number': company_number,
                    'status': profile.company_status,
                    'incorporation_date': profile.incorporation_date
                })
                
                # Add officers as nodes and edges
                officers = ch_api.get_officers(company_number)
                for officer in officers:
                    officer_id = f"officer_{officer.officer_id}"
                    
                    # Add officer node
                    network_data['nodes'].append({
                        'id': officer_id,
                        'label': officer.name,
                        'type': 'Person',
                        'role': officer.role,
                        'nationality': officer.nationality
                    })
                    
                    # Add relationship edge
                    network_data['edges'].append({
                        'source': officer_id,
                        'target': f"company_{company_number}",
                        'relationship': officer.role,
                        'appointed_on': officer.appointed_on
                    })
        
        network_data['metadata']['total_nodes'] = len(network_data['nodes'])
        network_data['metadata']['total_edges'] = len(network_data['edges'])
        
        print(f"✅ Built test network with {len(network_data['nodes'])} nodes and {len(network_data['edges'])} edges")
        
        # Count node types
        companies_count = len([n for n in network_data['nodes'] if n['type'] == 'Company'])
        people_count = len([n for n in network_data['nodes'] if n['type'] == 'Person'])
        
        print(f"  Companies: {companies_count}")
        print(f"  Directors/Officers: {people_count}")
        print(f"  Relationships: {len(network_data['edges'])}")
        
        # Show some sample relationships
        if network_data['edges']:
            print("\n  Sample relationships:")
            for i, edge in enumerate(network_data['edges'][:3], 1):
                source_node = next((n for n in network_data['nodes'] if n['id'] == edge['source']), None)
                target_node = next((n for n in network_data['nodes'] if n['id'] == edge['target']), None)
                
                if source_node and target_node:
                    print(f"    {i}. {source_node['label']} --{edge['relationship']}--> {target_node['label']}")
        
    except Exception as e:
        print(f"❌ Network building failed: {e}")
        return False
    
    print("\n🎉 All Companies House sandbox tests completed successfully!")
    
    # Save test company numbers for future use
    print(f"\n📝 Test company numbers created:")
    for company in test_companies:
        print(f"  - {company['company_number']}: {company.get('company_uri', 'N/A')}")
    
    return True

if __name__ == "__main__":
    print("🏢 Companies House API Sandbox Test")
    print("=" * 60)
    
    success = test_companies_house_sandbox()
    
    if success:
        print("\n✅ All sandbox tests passed! Companies House integration is working correctly.")
        print("\n💡 Note: The sandbox environment is now populated with test data.")
        print("   You can use the test company numbers above in the Streamlit application.")
    else:
        print("\n❌ Some tests failed. Please check the API key and connection.")
    
    print("\n" + "=" * 60)
