# UK Companies House API Integration Guide

## Overview

This guide explains how to integrate the UK Companies House API to build knowledge graphs focusing on:
- Company names and profiles
- Directors and officers
- Ultimate Beneficial Owners (UBOs) / Persons with Significant Control (PSCs)
- Business activities and SIC codes
- Corporate relationships and ownership structures

## Getting API Access

### 1. Register for API Key

1. **Create Account**: Go to [Companies House Developer Hub](https://developer.company-information.service.gov.uk/)
2. **Sign in/Register**: Click "Sign in / Register" and create a free account
3. **Create Application**: 
   - Sign in and click "Create an application"
   - Provide name: "Knowledge Graph Explorer"
   - Description: "Building corporate knowledge graphs"
   - Choose "Live application" for production use
4. **Create API Key**:
   - Select your application
   - Click "Create new key"
   - Choose "API key" type
   - Name it "KG Explorer API Key"
   - Copy and save the generated API key

### 2. API Authentication

Companies House API uses HTTP Basic Authentication:
- **Username**: Your API key
- **Password**: Empty string
- **Base URL**: `https://api.company-information.service.gov.uk`

## Key API Endpoints for Knowledge Graphs

### 1. Company Search & Profile
```
GET /search/companies?q={company_name}
GET /company/{company_number}
```

### 2. Directors & Officers
```
GET /company/{company_number}/officers
GET /company/{company_number}/appointments/{appointment_id}
```

### 3. Persons with Significant Control (UBOs)
```
GET /company/{company_number}/persons-with-significant-control
GET /company/{company_number}/persons-with-significant-control/individual/{psc_id}
GET /company/{company_number}/persons-with-significant-control/corporate-entity/{psc_id}
```

### 4. Filing History & Documents
```
GET /company/{company_number}/filing-history
```

## Python SDK Options

### Recommended: `companies-house-api-client`
```bash
pip install companies-house-api-client
```

### Alternative: `chwrapper`
```bash
pip install chwrapper
```

### Manual Implementation
Use `requests` library with basic authentication.

## Data Structure for Knowledge Graphs

### Company Node
```json
{
  "id": "company_number",
  "name": "company_name",
  "type": "Company",
  "status": "active/dissolved",
  "incorporation_date": "YYYY-MM-DD",
  "sic_codes": ["12345", "67890"],
  "business_activity": "Description of business",
  "registered_address": {
    "address_line_1": "...",
    "locality": "...",
    "postal_code": "..."
  }
}
```

### Director/Officer Node
```json
{
  "id": "officer_id",
  "name": "full_name",
  "type": "Person",
  "role": "director/secretary",
  "appointed_on": "YYYY-MM-DD",
  "nationality": "British",
  "occupation": "Director"
}
```

### PSC/UBO Node
```json
{
  "id": "psc_id",
  "name": "name",
  "type": "Person/Corporate",
  "nature_of_control": ["ownership-of-shares-25-to-50-percent"],
  "notified_on": "YYYY-MM-DD",
  "country_of_residence": "England"
}
```

### Relationships
- `DIRECTOR_OF`: Person → Company
- `CONTROLS`: PSC → Company  
- `OWNS_SHARES_IN`: Person/Company → Company
- `SUBSIDIARY_OF`: Company → Company
- `SAME_INDUSTRY`: Company → Company (via SIC codes)

## Rate Limits & Best Practices

- **Rate Limit**: 600 requests per 5 minutes
- **Caching**: Cache responses to minimize API calls
- **Batch Processing**: Process companies in batches
- **Error Handling**: Handle 404s for dissolved companies
- **Respect Terms**: Only use for legitimate business purposes

## Sample Implementation Structure

```python
class CompaniesHouseAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.company-information.service.gov.uk"
    
    def search_companies(self, query):
        # Search for companies by name
        pass
    
    def get_company_profile(self, company_number):
        # Get detailed company information
        pass
    
    def get_officers(self, company_number):
        # Get directors and officers
        pass
    
    def get_pscs(self, company_number):
        # Get persons with significant control
        pass
    
    def build_company_graph(self, company_name, depth=2):
        # Build multi-level knowledge graph
        pass
```

## Integration with Existing Exa Knowledge Graph

The Companies House integration can complement your Exa.ai knowledge graph by:

1. **Cross-referencing**: Match companies found via Exa with official Companies House data
2. **Enrichment**: Add official corporate structure data to web-scraped information
3. **Validation**: Verify company information accuracy
4. **Relationship Discovery**: Find corporate connections not visible in web content

## Next Steps

1. **Get API Key**: Register and obtain your Companies House API key
2. **Install SDK**: Choose and install a Python SDK
3. **Create Integration**: Build the Companies House page for your Streamlit app
4. **Test with Real Data**: Start with well-known companies like "Tesco PLC" or "BP PLC"
5. **Build Knowledge Graph**: Focus on director networks and ownership chains

This integration will provide authoritative UK corporate data to enhance your knowledge graph capabilities!
