#!/usr/bin/env python3
"""
Simple test script for Predictive Labs Ltd using Companies House API
This script will:
1. Search for Predictive Labs Ltd
2. Get company profile
3. Get officers/directors
4. Get PSCs (Ultimate Beneficial Owners)
5. Save all responses to test-data directory
6. Print summary of findings
"""

import json
import os
from utils.companies_house_api import CompaniesHouseAPI

def save_json_response(data, filename):
    """Save JSON response to test-data directory"""
    os.makedirs('test-data', exist_ok=True)
    filepath = os.path.join('test-data', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved response to: {filepath}")

def main():
    print("🔍 Testing Companies House API with Predictive Labs Ltd")
    print("=" * 60)
    
    # Initialize API client
    api_key = os.environ.get('CH_API_KEY', 'ccd402e3-9dc9-4d47-b348-6decb7b18dea')
    client = CompaniesHouseAPI(api_key=api_key, use_sandbox=False)
    
    company_name = "Predictive Labs Ltd"
    print(f"🏢 Searching for: {company_name}")
    
    # 1. Search for the company
    print("\n1️⃣ Searching for companies...")
    search_results = client.search_companies(company_name, items_per_page=5)
    
    if search_results:
        print(f"   Found {len(search_results)} companies")
        save_json_response({
            "query": company_name,
            "total_results": len(search_results),
            "items": search_results
        }, "predictive_labs_search.json")
        
        # Find the exact match or best match
        target_company = None
        for company in search_results:
            if "predictive labs" in company.get('title', '').lower():
                target_company = company
                break
        
        if not target_company:
            target_company = search_results[0]  # Take first result
        
        company_number = target_company['company_number']
        company_title = target_company['title']
        
        print(f"   Selected: {company_title} (Company Number: {company_number})")
        
        # 2. Get company profile
        print(f"\n2️⃣ Getting company profile for {company_number}...")
        profile = client.get_company_profile(company_number)
        
        if profile:
            print(f"   Company Name: {profile.company_name}")
            print(f"   Status: {profile.company_status}")
            print(f"   Type: {profile.company_type}")
            print(f"   Incorporated: {profile.incorporation_date}")
            print(f"   SIC Codes: {profile.sic_codes}")
            
            # Convert dataclass to dict for JSON serialization
            profile_dict = {
                'company_number': profile.company_number,
                'company_name': profile.company_name,
                'company_status': profile.company_status,
                'company_type': profile.company_type,
                'incorporation_date': profile.incorporation_date,
                'sic_codes': profile.sic_codes,
                'registered_address': profile.registered_address,
                'business_activity': profile.business_activity
            }
            save_json_response(profile_dict, "predictive_labs_profile.json")
        else:
            print("   ❌ Could not retrieve company profile")
        
        # 3. Get officers/directors
        print(f"\n3️⃣ Getting officers for {company_number}...")
        officers = client.get_officers(company_number)
        
        if officers:
            print(f"   Found {len(officers)} officers:")
            for officer in officers:
                print(f"   - {officer.name} ({officer.role})")
                if officer.appointed_on:
                    print(f"     Appointed: {officer.appointed_on}")
                if officer.nationality:
                    print(f"     Nationality: {officer.nationality}")
            
            # Convert dataclass list to dict for JSON serialization
            officers_dict = {
                "total_results": len(officers),
                "items": []
            }
            
            for officer in officers:
                officer_dict = {
                    'officer_id': officer.officer_id,
                    'name': officer.name,
                    'officer_role': officer.role,
                    'appointed_on': officer.appointed_on,
                    'resigned_on': officer.resigned_on,
                    'nationality': officer.nationality,
                    'occupation': officer.occupation,
                    'country_of_residence': officer.country_of_residence
                }
                officers_dict["items"].append(officer_dict)
            
            save_json_response(officers_dict, "predictive_labs_officers.json")
        else:
            print("   ❌ Could not retrieve officers")
        
        # 4. Get PSCs (Ultimate Beneficial Owners)
        print(f"\n4️⃣ Getting PSCs (Ultimate Beneficial Owners) for {company_number}...")
        pscs = client.get_pscs(company_number)
        
        if pscs:
            print(f"   Found {len(pscs)} PSCs:")
            for psc in pscs:
                print(f"   - {psc.name} ({psc.psc_type})")
                print(f"     Nature of Control: {psc.nature_of_control}")
                if psc.nationality:
                    print(f"     Nationality: {psc.nationality}")
            
            # Convert dataclass list to dict for JSON serialization
            pscs_dict = {
                "total_results": len(pscs),
                "items": []
            }
            
            for psc in pscs:
                psc_dict = {
                    'psc_id': psc.psc_id,
                    'name': psc.name,
                    'kind': f"{psc.psc_type}-person-with-significant-control",
                    'natures_of_control': psc.nature_of_control,
                    'notified_on': psc.notified_on,
                    'country_of_residence': psc.country_of_residence,
                    'nationality': psc.nationality
                }
                pscs_dict["items"].append(psc_dict)
            
            save_json_response(pscs_dict, "predictive_labs_pscs.json")
        else:
            print("   ❌ Could not retrieve PSCs")
        
        # 5. Summary
        print(f"\n📊 SUMMARY FOR {company_title}")
        print("=" * 60)
        print(f"Company Number: {company_number}")
        if profile:
            print(f"Status: {profile.company_status}")
            print(f"Incorporated: {profile.incorporation_date}")
            print(f"Business Activity: {profile.sic_codes}")
        print(f"Officers: {len(officers) if officers else 0}")
        print(f"PSCs/UBOs: {len(pscs) if pscs else 0}")
        
        print(f"\n💾 All data saved to test-data/ directory:")
        print("   - predictive_labs_search.json")
        print("   - predictive_labs_profile.json") 
        print("   - predictive_labs_officers.json")
        print("   - predictive_labs_pscs.json")
        
    else:
        print("   ❌ No companies found")

if __name__ == "__main__":
    main()
