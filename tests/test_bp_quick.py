#!/usr/bin/env python3
"""
Quick test script for BP PLC to demonstrate Companies House API with different company
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from companies_house_api import CompaniesHouseAPI

def test_bp_company():
    """Test BP PLC specifically"""
    
    # Get API key from environment
    api_key = os.getenv('CH_API_KEY')
    if not api_key:
        print("❌ CH_API_KEY not found in environment variables")
        return False
    
    print(f"🔑 Testing BP PLC with API key: {api_key[:8]}...")
    
    # Initialize API client for live environment
    ch_api = CompaniesHouseAPI(api_key, use_sandbox=False)
    print("✅ Companies House API client initialized (Live production mode)")
    
    # Test BP PLC specifically
    print(f"\n🏢 Testing BP P.L.C. (Company Number: 00102498)")
    
    try:
        # Get company profile
        profile = ch_api.get_company_profile("00102498")
        if profile:
            print(f"✅ Retrieved profile for {profile.company_name}")
            print(f"  Company Number: {profile.company_number}")
            print(f"  Status: {profile.company_status}")
            print(f"  Incorporation Date: {profile.incorporation_date}")
            print(f"  Company Type: {profile.company_type}")
            print(f"  SIC Codes: {', '.join(profile.sic_codes) if profile.sic_codes else 'None'}")
            print(f"  Business Activity: {profile.business_activity or 'N/A'}")
            
            if profile.registered_address:
                print(f"  Registered Address: {profile.registered_address.get('address_line_1', 'N/A')}")
                print(f"                     {profile.registered_address.get('locality', 'N/A')}, {profile.registered_address.get('postal_code', 'N/A')}")
        
        # Get officers
        officers = ch_api.get_officers("00102498")
        print(f"\n👥 Found {len(officers)} officers for BP P.L.C.")
        
        for i, officer in enumerate(officers[:3], 1):  # Show first 3 officers
            print(f"  {i}. {officer.name}")
            print(f"     Role: {officer.role}")
            print(f"     Appointed: {officer.appointed_on or 'N/A'}")
            print(f"     Nationality: {officer.nationality or 'N/A'}")
        
        # Build network
        print(f"\n🕸️ Building BP company network...")
        network = ch_api.get_company_network("BP", max_companies=2)
        
        if network and network['nodes']:
            companies_count = len([n for n in network['nodes'] if n['type'] == 'Company'])
            people_count = len([n for n in network['nodes'] if n['type'] == 'Person'])
            psc_count = len([n for n in network['nodes'] if n['type'] == 'PSC'])
            
            print(f"✅ Built BP network: {len(network['nodes'])} nodes, {len(network['edges'])} edges")
            print(f"  📊 Companies: {companies_count}, People: {people_count}, PSCs: {psc_count}")
            
            # Show some relationships
            print(f"  🔗 Sample Relationships:")
            for i, edge in enumerate(network['edges'][:3], 1):
                source_node = next((n for n in network['nodes'] if n['id'] == edge['source']), None)
                target_node = next((n for n in network['nodes'] if n['id'] == edge['target']), None)
                
                if source_node and target_node:
                    print(f"    {i}. {source_node['label']} --[{edge['relationship']}]--> {target_node['label']}")
        
        print(f"\n🎉 BP P.L.C. test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ BP test failed: {e}")
        return False

if __name__ == "__main__":
    print("🏢 BP P.L.C. Companies House API Test")
    print("=" * 50)
    
    success = test_bp_company()
    
    if success:
        print("\n✅ BP test passed! Ready for Streamlit testing.")
    else:
        print("\n❌ BP test failed.")
    
    print("=" * 50)
