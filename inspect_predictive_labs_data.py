#!/usr/bin/env python3
"""
Inspection script for Predictive Labs Ltd data
Analyzes the JSON files saved from the Companies House API
"""

import json
import os
from datetime import datetime

def load_json(filename):
    """Load JSON file from test-data directory"""
    filepath = os.path.join('test-data', filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def analyze_search_data():
    """Analyze search results"""
    print("🔍 SEARCH RESULTS ANALYSIS")
    print("=" * 50)
    
    data = load_json('predictive_labs_search.json')
    if not data:
        print("❌ Search data not found")
        return
    
    print(f"Query: {data['query']}")
    print(f"Total Results: {data['total_results']}")
    print("\nCompanies found:")
    
    for i, company in enumerate(data['items'], 1):
        print(f"\n{i}. {company['title']}")
        print(f"   Company Number: {company['company_number']}")
        print(f"   Status: {company['company_status']}")
        print(f"   Type: {company['company_type']}")
        print(f"   Incorporated: {company['date_of_creation']}")
        print(f"   Address: {company['address_snippet']}")
        
        if company['company_status'] == 'dissolved':
            print(f"   ⚠️  Dissolved: {company.get('date_of_cessation', 'Unknown')}")

def analyze_profile_data():
    """Analyze company profile"""
    print("\n\n🏢 COMPANY PROFILE ANALYSIS")
    print("=" * 50)
    
    data = load_json('predictive_labs_profile.json')
    if not data:
        print("❌ Profile data not found")
        return
    
    print(f"Company Name: {data['company_name']}")
    print(f"Company Number: {data['company_number']}")
    print(f"Status: {data['company_status']}")
    print(f"Type: {data['company_type']}")
    print(f"Incorporated: {data['incorporation_date']}")
    
    # Calculate company age
    inc_date = datetime.strptime(data['incorporation_date'], '%Y-%m-%d')
    age_days = (datetime.now() - inc_date).days
    age_years = age_days / 365.25
    print(f"Company Age: {age_years:.1f} years ({age_days} days)")
    
    print(f"\nSIC Codes: {data['sic_codes']}")
    print(f"Business Activity: {data['business_activity']}")
    
    print(f"\nRegistered Address:")
    address = data['registered_address']
    for key, value in address.items():
        if value:
            print(f"  {key.replace('_', ' ').title()}: {value}")

def analyze_officers_data():
    """Analyze officers/directors"""
    print("\n\n👥 OFFICERS/DIRECTORS ANALYSIS")
    print("=" * 50)
    
    data = load_json('predictive_labs_officers.json')
    if not data:
        print("❌ Officers data not found")
        return
    
    print(f"Total Officers: {data['total_results']}")
    
    for i, officer in enumerate(data['items'], 1):
        print(f"\n{i}. {officer['name']}")
        print(f"   Role: {officer['officer_role']}")
        print(f"   Appointed: {officer['appointed_on']}")
        
        if officer['resigned_on']:
            print(f"   Resigned: {officer['resigned_on']}")
        else:
            print(f"   Status: Active")
        
        if officer['nationality']:
            print(f"   Nationality: {officer['nationality']}")
        
        if officer['occupation']:
            print(f"   Occupation: {officer['occupation']}")
        
        if officer['country_of_residence']:
            print(f"   Residence: {officer['country_of_residence']}")

def analyze_pscs_data():
    """Analyze PSCs (Ultimate Beneficial Owners)"""
    print("\n\n🎯 PSCs/UBOs ANALYSIS")
    print("=" * 50)
    
    data = load_json('predictive_labs_pscs.json')
    if not data:
        print("❌ PSCs data not found")
        return
    
    print(f"Total PSCs: {data['total_results']}")
    
    for i, psc in enumerate(data['items'], 1):
        print(f"\n{i}. {psc['name']}")
        print(f"   Type: {psc['kind']}")
        print(f"   Notified: {psc['notified_on']}")
        
        if psc['nationality']:
            print(f"   Nationality: {psc['nationality']}")
        
        if psc['country_of_residence']:
            print(f"   Residence: {psc['country_of_residence']}")
        
        print(f"   Nature of Control:")
        for control in psc['natures_of_control']:
            control_desc = control.replace('-', ' ').replace('_', ' ').title()
            print(f"     • {control_desc}")

def analyze_business_activity():
    """Analyze business activity using SIC codes"""
    print("\n\n📊 BUSINESS ACTIVITY ANALYSIS")
    print("=" * 50)
    
    profile_data = load_json('predictive_labs_profile.json')
    if not profile_data:
        print("❌ Profile data not found")
        return
    
    sic_codes = profile_data.get('sic_codes', [])
    print(f"SIC Codes: {sic_codes}")
    
    # SIC code descriptions (common ones)
    sic_descriptions = {
        '70229': 'Management consultancy activities other than financial management',
        '62012': 'Business and domestic software development',
        '62020': 'Information technology consultancy activities',
        '72190': 'Other research and experimental development on natural sciences and engineering',
        '63110': 'Data processing, hosting and related activities'
    }
    
    for code in sic_codes:
        if code in sic_descriptions:
            print(f"  {code}: {sic_descriptions[code]}")
        else:
            print(f"  {code}: (Description not available)")

def generate_summary():
    """Generate overall summary"""
    print("\n\n📋 OVERALL SUMMARY")
    print("=" * 50)
    
    profile_data = load_json('predictive_labs_profile.json')
    officers_data = load_json('predictive_labs_officers.json')
    pscs_data = load_json('predictive_labs_pscs.json')
    
    if profile_data:
        print(f"Company: {profile_data['company_name']}")
        print(f"Status: {profile_data['company_status']}")
        print(f"Incorporated: {profile_data['incorporation_date']}")
    
    if officers_data:
        print(f"Officers: {officers_data['total_results']}")
    
    if pscs_data:
        print(f"PSCs/UBOs: {pscs_data['total_results']}")
    
    print(f"\nData Quality:")
    files = ['predictive_labs_search.json', 'predictive_labs_profile.json', 
             'predictive_labs_officers.json', 'predictive_labs_pscs.json']
    
    for filename in files:
        if load_json(filename):
            print(f"  ✅ {filename}")
        else:
            print(f"  ❌ {filename}")

def main():
    print("🔍 PREDICTIVE LABS LTD - DATA INSPECTION")
    print("=" * 60)
    
    analyze_search_data()
    analyze_profile_data()
    analyze_officers_data()
    analyze_pscs_data()
    analyze_business_activity()
    generate_summary()
    
    print(f"\n💾 Raw JSON files available in test-data/ directory")

if __name__ == "__main__":
    main()
