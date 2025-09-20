#!/usr/bin/env python3
"""
Live test script for Companies House API integration
Tests the API with real data using the provided API key
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from companies_house_api import CompaniesHouseAPI

def test_companies_house_api():
    """Test the Companies House API with real data"""
    
    # Get API key from environment
    api_key = os.getenv('CH_API_KEY')
    if not api_key:
        print("❌ CH_API_KEY not found in environment variables")
        return False
    
    print(f"🔑 Using API key: {api_key[:8]}...")
    
    # Initialize API client
    try:
        ch_api = CompaniesHouseAPI(api_key)
        print("✅ Companies House API client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize API client: {e}")
        return False
    
    # Test 1: Search for companies
    print("\n🔍 Testing company search...")
    try:
        companies = ch_api.search_companies("Tesco", items_per_page=5)
        print(f"✅ Found {len(companies)} companies matching 'Tesco'")
        
        if companies:
            for i, company in enumerate(companies[:3], 1):
                print(f"  {i}. {company.get('title', 'N/A')} ({company.get('company_number', 'N/A')})")
                print(f"     Status: {company.get('company_status', 'N/A')}")
                print(f"     Type: {company.get('company_type', 'N/A')}")
        else:
            print("⚠️ No companies found")
            
    except Exception as e:
        print(f"❌ Company search failed: {e}")
        return False
    
    # Test 2: Get company profile
    if companies:
        test_company = companies[0]
        company_number = test_company.get('company_number')
        
        print(f"\n🏢 Testing company profile for {company_number}...")
        try:
            profile = ch_api.get_company_profile(company_number)
            if profile:
                print(f"✅ Retrieved profile for {profile.company_name}")
                print(f"  Status: {profile.company_status}")
                print(f"  Incorporation: {profile.incorporation_date}")
                print(f"  SIC Codes: {', '.join(profile.sic_codes) if profile.sic_codes else 'None'}")
                print(f"  Business Activity: {profile.business_activity or 'N/A'}")
            else:
                print("⚠️ No profile data retrieved")
        except Exception as e:
            print(f"❌ Profile retrieval failed: {e}")
            return False
        
        # Test 3: Get officers
        print(f"\n👥 Testing officers for {company_number}...")
        try:
            officers = ch_api.get_officers(company_number)
            print(f"✅ Found {len(officers)} officers")
            
            for i, officer in enumerate(officers[:3], 1):
                print(f"  {i}. {officer.name}")
                print(f"     Role: {officer.role}")
                print(f"     Appointed: {officer.appointed_on or 'N/A'}")
                print(f"     Nationality: {officer.nationality or 'N/A'}")
                
        except Exception as e:
            print(f"❌ Officers retrieval failed: {e}")
            return False
        
        # Test 4: Get PSCs (Persons with Significant Control)
        print(f"\n🎯 Testing PSCs for {company_number}...")
        try:
            pscs = ch_api.get_pscs(company_number)
            print(f"✅ Found {len(pscs)} PSCs")
            
            for i, psc in enumerate(pscs[:3], 1):
                print(f"  {i}. {psc.name}")
                print(f"     Type: {psc.psc_type}")
                print(f"     Control: {', '.join(psc.nature_of_control) if psc.nature_of_control else 'N/A'}")
                print(f"     Notified: {psc.notified_on or 'N/A'}")
                
        except Exception as e:
            print(f"❌ PSCs retrieval failed: {e}")
            return False
    
    # Test 5: Build company network
    print(f"\n🕸️ Testing company network building...")
    try:
        network = ch_api.get_company_network("Tesco", max_companies=3)
        
        if network and network['nodes']:
            print(f"✅ Built network with {len(network['nodes'])} nodes and {len(network['edges'])} edges")
            
            # Count node types
            companies_count = len([n for n in network['nodes'] if n['type'] == 'Company'])
            people_count = len([n for n in network['nodes'] if n['type'] == 'Person'])
            psc_count = len([n for n in network['nodes'] if n['type'] == 'PSC'])
            
            print(f"  Companies: {companies_count}")
            print(f"  Directors/Officers: {people_count}")
            print(f"  PSCs/UBOs: {psc_count}")
            print(f"  Relationships: {len(network['edges'])}")
            
            # Show some sample relationships
            print("\n  Sample relationships:")
            for i, edge in enumerate(network['edges'][:3], 1):
                source_node = next((n for n in network['nodes'] if n['id'] == edge['source']), None)
                target_node = next((n for n in network['nodes'] if n['id'] == edge['target']), None)
                
                if source_node and target_node:
                    print(f"    {i}. {source_node['label']} --{edge['relationship']}--> {target_node['label']}")
        else:
            print("⚠️ No network data generated")
            
    except Exception as e:
        print(f"❌ Network building failed: {e}")
        return False
    
    print("\n🎉 All Companies House API tests completed successfully!")
    return True

if __name__ == "__main__":
    print("🏢 Companies House API Live Test")
    print("=" * 50)
    
    success = test_companies_house_api()
    
    if success:
        print("\n✅ All tests passed! Companies House integration is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the API key and connection.")
    
    print("\n" + "=" * 50)
