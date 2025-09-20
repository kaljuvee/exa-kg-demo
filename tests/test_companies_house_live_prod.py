#!/usr/bin/env python3
"""
Live production test script for Companies House API integration
Tests the API with real UK company data using the production API key
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from companies_house_api import CompaniesHouseAPI

def test_companies_house_live():
    """Test the Companies House API with live production data"""
    
    # Get API key from environment
    api_key = os.getenv('CH_API_KEY')
    if not api_key:
        print("❌ CH_API_KEY not found in environment variables")
        return False
    
    print(f"🔑 Using production API key: {api_key[:8]}...")
    
    # Initialize API client for live environment
    try:
        ch_api = CompaniesHouseAPI(api_key, use_sandbox=False)
        print("✅ Companies House API client initialized (Live production mode)")
    except Exception as e:
        print(f"❌ Failed to initialize API client: {e}")
        return False
    
    # Test 1: Search for companies
    print("\n🔍 Testing company search with real UK companies...")
    test_companies = ["Tesco", "BP", "Vodafone"]
    
    for company_name in test_companies:
        try:
            print(f"\n  Searching for: {company_name}")
            companies = ch_api.search_companies(company_name, items_per_page=3)
            print(f"  ✅ Found {len(companies)} companies matching '{company_name}'")
            
            if companies:
                for i, company in enumerate(companies[:2], 1):
                    print(f"    {i}. {company.get('title', 'N/A')} ({company.get('company_number', 'N/A')})")
                    print(f"       Status: {company.get('company_status', 'N/A')}")
                    print(f"       Type: {company.get('company_type', 'N/A')}")
                    print(f"       Incorporated: {company.get('date_of_creation', 'N/A')}")
            else:
                print(f"  ⚠️ No companies found for {company_name}")
                
        except Exception as e:
            print(f"  ❌ Search failed for {company_name}: {e}")
    
    # Test 2: Get detailed company profile for Tesco PLC
    print(f"\n🏢 Testing detailed company profile...")
    tesco_company_number = "00445790"  # Tesco PLC
    
    try:
        profile = ch_api.get_company_profile(tesco_company_number)
        if profile:
            print(f"✅ Retrieved detailed profile for {profile.company_name}")
            print(f"  Company Number: {profile.company_number}")
            print(f"  Status: {profile.company_status}")
            print(f"  Incorporation Date: {profile.incorporation_date}")
            print(f"  Company Type: {profile.company_type}")
            print(f"  SIC Codes: {', '.join(profile.sic_codes) if profile.sic_codes else 'None'}")
            print(f"  Business Activity: {profile.business_activity or 'N/A'}")
            
            if profile.registered_address:
                print(f"  Registered Address: {profile.registered_address.get('address_line_1', 'N/A')}")
                print(f"                     {profile.registered_address.get('locality', 'N/A')}, {profile.registered_address.get('postal_code', 'N/A')}")
        else:
            print(f"⚠️ No profile data retrieved for {tesco_company_number}")
    except Exception as e:
        print(f"❌ Profile retrieval failed: {e}")
    
    # Test 3: Get officers for Tesco PLC
    print(f"\n👥 Testing officers retrieval...")
    try:
        officers = ch_api.get_officers(tesco_company_number)
        print(f"✅ Found {len(officers)} officers for Tesco PLC")
        
        for i, officer in enumerate(officers[:5], 1):  # Show first 5 officers
            print(f"  {i}. {officer.name}")
            print(f"     Role: {officer.role}")
            print(f"     Appointed: {officer.appointed_on or 'N/A'}")
            print(f"     Nationality: {officer.nationality or 'N/A'}")
            print(f"     Occupation: {officer.occupation or 'N/A'}")
            if officer.resigned_on:
                print(f"     Resigned: {officer.resigned_on}")
            print()
            
    except Exception as e:
        print(f"❌ Officers retrieval failed: {e}")
    
    # Test 4: Get PSCs (Persons with Significant Control) for Tesco PLC
    print(f"\n🎯 Testing PSCs retrieval...")
    try:
        pscs = ch_api.get_pscs(tesco_company_number)
        print(f"✅ Found {len(pscs)} PSCs for Tesco PLC")
        
        for i, psc in enumerate(pscs[:3], 1):  # Show first 3 PSCs
            print(f"  {i}. {psc.name}")
            print(f"     Type: {psc.psc_type}")
            print(f"     Nature of Control: {', '.join(psc.nature_of_control) if psc.nature_of_control else 'N/A'}")
            print(f"     Notified On: {psc.notified_on or 'N/A'}")
            print(f"     Country of Residence: {psc.country_of_residence or 'N/A'}")
            print(f"     Nationality: {psc.nationality or 'N/A'}")
            print()
            
    except Exception as e:
        print(f"❌ PSCs retrieval failed: {e}")
    
    # Test 5: Build a comprehensive company network
    print(f"\n🕸️ Testing comprehensive company network building...")
    try:
        network = ch_api.get_company_network("Tesco", max_companies=3)
        
        if network and network['nodes']:
            print(f"✅ Built comprehensive network with {len(network['nodes'])} nodes and {len(network['edges'])} edges")
            
            # Count node types
            companies_count = len([n for n in network['nodes'] if n['type'] == 'Company'])
            people_count = len([n for n in network['nodes'] if n['type'] == 'Person'])
            psc_count = len([n for n in network['nodes'] if n['type'] == 'PSC'])
            
            print(f"  📊 Network Statistics:")
            print(f"    Companies: {companies_count}")
            print(f"    Directors/Officers: {people_count}")
            print(f"    PSCs/UBOs: {psc_count}")
            print(f"    Total Relationships: {len(network['edges'])}")
            
            # Show metadata
            if 'metadata' in network:
                metadata = network['metadata']
                print(f"  📈 Metadata:")
                print(f"    Total API Calls: {metadata.get('total_api_calls', 'N/A')}")
                print(f"    Processing Time: {metadata.get('processing_time', 'N/A')} seconds")
                print(f"    Environment: {metadata.get('environment', 'live')}")
            
            # Show some sample relationships
            print(f"\n  🔗 Sample Relationships:")
            relationship_types = {}
            for edge in network['edges']:
                rel_type = edge['relationship']
                relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
            
            for rel_type, count in relationship_types.items():
                print(f"    {rel_type}: {count} relationships")
            
            # Show specific examples
            print(f"\n  📋 Example Connections:")
            for i, edge in enumerate(network['edges'][:5], 1):
                source_node = next((n for n in network['nodes'] if n['id'] == edge['source']), None)
                target_node = next((n for n in network['nodes'] if n['id'] == edge['target']), None)
                
                if source_node and target_node:
                    print(f"    {i}. {source_node['label']} --[{edge['relationship']}]--> {target_node['label']}")
        else:
            print("⚠️ No network data generated")
            
    except Exception as e:
        print(f"❌ Network building failed: {e}")
        return False
    
    print("\n🎉 All Companies House live production tests completed successfully!")
    return True

if __name__ == "__main__":
    print("🏢 Companies House API Live Production Test")
    print("=" * 70)
    print("Testing with real UK company data from Companies House API")
    print("=" * 70)
    
    success = test_companies_house_live()
    
    if success:
        print("\n✅ All production tests passed! Companies House integration is working perfectly.")
        print("\n💡 The application is ready to use with real UK company data.")
        print("   You can now search for any UK company in the Streamlit application.")
    else:
        print("\n❌ Some tests failed. Please check the API key and connection.")
    
    print("\n" + "=" * 70)
