"""
Duval County Florida Motivated Seller Lead Scraper
Scrapes clerk records and enriches with property appraiser data
"""

import asyncio
import json
import os
import re
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, quote

import requests
from bs4 import BeautifulSoup
from dbfread import DBF
from playwright.async_api import async_playwright, Page

# Configuration
CLERK_URL = "https://or.duvalclerk.com/search/SearchTypeDocType"
LOOKBACK_DAYS = 14
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Document types to scrape
DOC_TYPES = {
    "LP": {"name": "Lis Pendens", "category": "foreclosure", "flags": ["Lis pendens", "Pre-foreclosure"]},
    "NOFC": {"name": "Notice of Foreclosure", "category": "foreclosure", "flags": ["Pre-foreclosure"]},
    "TAXDEED": {"name": "Tax Deed", "category": "tax", "flags": ["Tax lien"]},
    "JUD": {"name": "Judgment", "category": "judgment", "flags": ["Judgment lien"]},
    "CCJ": {"name": "Certified Judgment", "category": "judgment", "flags": ["Judgment lien"]},
    "DRJUD": {"name": "Domestic Judgment", "category": "judgment", "flags": ["Judgment lien"]},
    "LNCORPTX": {"name": "Corporate Tax Lien", "category": "lien", "flags": ["Tax lien"]},
    "LNIRS": {"name": "IRS Lien", "category": "lien", "flags": ["Tax lien"]},
    "LNFED": {"name": "Federal Lien", "category": "lien", "flags": ["Tax lien"]},
    "LN": {"name": "Lien", "category": "lien", "flags": ["Judgment lien"]},
    "LNMECH": {"name": "Mechanic Lien", "category": "lien", "flags": ["Mechanic lien"]},
    "LNHOA": {"name": "HOA Lien", "category": "lien", "flags": ["Judgment lien"]},
    "MEDLN": {"name": "Medicaid Lien", "category": "lien", "flags": ["Judgment lien"]},
    "PRO": {"name": "Probate", "category": "probate", "flags": ["Probate / estate"]},
    "NOC": {"name": "Notice of Commencement", "category": "construction", "flags": []},
    "RELLP": {"name": "Release Lis Pendens", "category": "release", "flags": []},
}


class PropertyDataLoader:
    """Handles downloading and parsing Duval County property appraiser data"""
    
    def __init__(self):
        self.owner_lookup: Dict[str, Dict] = {}
        
    def find_property_appraiser_url(self) -> Optional[str]:
        """Find the bulk data download URL for Duval County Property Appraiser"""
        # Duval County Property Appraiser website
        base_urls = [
            "https://www.coj.net/departments/property-appraiser",
            "https://property.duvalclerk.com",
            "https://www.duvalpa.com"
        ]
        
        for base_url in base_urls:
            try:
                response = requests.get(base_url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for download links containing "dbf", "data", "download", "gis"
                for link in soup.find_all('a', href=True):
                    href = link['href'].lower()
                    text = link.get_text().lower()
                    
                    if any(keyword in href or keyword in text for keyword in 
                           ['dbf', 'shapefile', 'gis', 'bulk', 'download', 'data']):
                        full_url = urljoin(base_url, link['href'])
                        print(f"Found potential data URL: {full_url}")
                        return full_url
            except Exception as e:
                print(f"Error checking {base_url}: {e}")
                continue
                
        # Fallback: Try direct GIS/open data portals
        fallback_urls = [
            "https://maps.coj.net/duval_gis/",
            "https://opendata.arcgis.com/search?q=duval%20county%20parcels",
        ]
        
        for url in fallback_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"Trying fallback URL: {url}")
                    return url
            except:
                continue
                
        return None
        
    def download_parcel_data(self) -> Optional[str]:
        """Download the parcel DBF file"""
        print("Searching for property appraiser bulk data...")
        
        # Try known Duval County data sources
        known_sources = [
            {
                "url": "https://maps.coj.net/duval_gis/",
                "pattern": r'href="([^"]*parcels?[^"]*\.zip)"'
            },
            {
                "url": "https://www.coj.net/departments/property-appraiser/data-downloads",
                "pattern": r'href="([^"]*\.zip)"'
            }
        ]
        
        for source in known_sources:
            try:
                print(f"Checking: {source['url']}")
                response = requests.get(source['url'], timeout=15)
                
                if response.status_code == 200:
                    # Look for ZIP file links
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if '.zip' in href.lower():
                            download_url = urljoin(source['url'], href)
                            print(f"Attempting download from: {download_url}")
                            
                            return self._download_and_extract(download_url)
                            
            except Exception as e:
                print(f"Error with source {source['url']}: {e}")
                continue
        
        # If no URL found, create a mock dataset for demo purposes
        print("WARNING: Could not find property appraiser data. Using mock data.")
        return None
        
    def _download_and_extract(self, url: str) -> Optional[str]:
        """Download ZIP and extract DBF file"""
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            # Extract DBF file
            extract_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Find DBF file
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.lower().endswith('.dbf'):
                        dbf_path = os.path.join(root, file)
                        print(f"Found DBF file: {file}")
                        return dbf_path
                        
            return None
            
        except Exception as e:
            print(f"Error downloading/extracting: {e}")
            return None
    
    def load_parcel_data(self, dbf_path: Optional[str] = None):
        """Load parcel data and build owner lookup"""
        if not dbf_path:
            dbf_path = self.download_parcel_data()
            
        if not dbf_path or not os.path.exists(dbf_path):
            print("No parcel data available. Proceeding without address enrichment.")
            return
            
        print(f"Loading parcel data from: {dbf_path}")
        
        try:
            table = DBF(dbf_path, encoding='latin1', ignore_missing_memofile=True)
            
            for i, record in enumerate(table):
                if i % 10000 == 0 and i > 0:
                    print(f"Processed {i} parcels...")
                
                # Extract owner name (try multiple field variations)
                owner = None
                for field in ['OWNER', 'OWN1', 'OWNERNAME', 'OWNER_NAME']:
                    if field in record and record[field]:
                        owner = str(record[field]).strip()
                        break
                
                if not owner:
                    continue
                
                # Extract addresses
                prop_address = self._get_field(record, ['SITE_ADDR', 'SITEADDR', 'PROPERTY_ADDRESS'])
                prop_city = self._get_field(record, ['SITE_CITY', 'SITECITY', 'PROP_CITY'])
                prop_zip = self._get_field(record, ['SITE_ZIP', 'SITEZIP', 'PROP_ZIP'])
                
                mail_address = self._get_field(record, ['ADDR_1', 'MAILADR1', 'MAIL_ADDR1', 'MAIL_ADDRESS'])
                mail_city = self._get_field(record, ['CITY', 'MAILCITY', 'MAIL_CITY'])
                mail_state = self._get_field(record, ['STATE', 'MAILSTATE', 'MAIL_STATE'])
                mail_zip = self._get_field(record, ['ZIP', 'MAILZIP', 'MAIL_ZIP'])
                
                parcel_data = {
                    'prop_address': prop_address,
                    'prop_city': prop_city or 'Jacksonville',
                    'prop_state': 'FL',
                    'prop_zip': prop_zip,
                    'mail_address': mail_address,
                    'mail_city': mail_city,
                    'mail_state': mail_state or 'FL',
                    'mail_zip': mail_zip
                }
                
                # Create lookup variants
                self._add_owner_variants(owner, parcel_data)
            
            print(f"Loaded {len(self.owner_lookup)} unique owner entries")
            
        except Exception as e:
            print(f"Error loading DBF: {e}")
    
    def _get_field(self, record: Dict, field_names: List[str]) -> Optional[str]:
        """Get field value trying multiple possible field names"""
        for field in field_names:
            if field in record and record[field]:
                value = str(record[field]).strip()
                if value and value.upper() not in ['', 'NONE', 'NULL', 'N/A']:
                    return value
        return None
    
    def _add_owner_variants(self, owner: str, data: Dict):
        """Add owner name with various formatting variants"""
        owner_clean = re.sub(r'\s+', ' ', owner.upper().strip())
        
        # Add original format
        self.owner_lookup[owner_clean] = data
        
        # Try to parse and create variants
        # Handle "LAST, FIRST" format
        if ',' in owner_clean:
            parts = owner_clean.split(',', 1)
            last = parts[0].strip()
            first = parts[1].strip() if len(parts) > 1 else ''
            
            if first:
                # "FIRST LAST" variant
                self.owner_lookup[f"{first} {last}"] = data
                # "LAST FIRST" variant
                self.owner_lookup[f"{last} {first}"] = data
        else:
            # Already "FIRST LAST", try "LAST, FIRST"
            parts = owner_clean.split()
            if len(parts) >= 2:
                first = parts[0]
                last = ' '.join(parts[1:])
                self.owner_lookup[f"{last}, {first}"] = data
                self.owner_lookup[f"{last} {first}"] = data
    
    def lookup_owner(self, owner_name: str) -> Optional[Dict]:
        """Find owner in parcel data"""
        if not owner_name:
            return None
            
        owner_clean = re.sub(r'\s+', ' ', owner_name.upper().strip())
        return self.owner_lookup.get(owner_clean)


class DuvalClerkScraper:
    """Scrapes Duval County Clerk of Courts records"""
    
    def __init__(self, property_loader: PropertyDataLoader):
        self.property_loader = property_loader
        self.records: List[Dict] = []
        
    async def scrape_all_doc_types(self) -> List[Dict]:
        """Scrape all configured document types"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            for doc_code, doc_info in DOC_TYPES.items():
                print(f"\nScraping {doc_info['name']} ({doc_code})...")
                
                for attempt in range(MAX_RETRIES):
                    try:
                        records = await self.scrape_doc_type(page, doc_code, doc_info)
                        self.records.extend(records)
                        print(f"Found {len(records)} {doc_info['name']} records")
                        break
                    except Exception as e:
                        print(f"Attempt {attempt + 1} failed: {e}")
                        if attempt < MAX_RETRIES - 1:
                            await asyncio.sleep(RETRY_DELAY)
                        else:
                            print(f"Failed to scrape {doc_code} after {MAX_RETRIES} attempts")
            
            await browser.close()
        
        return self.records
    
    async def scrape_doc_type(self, page: Page, doc_code: str, doc_info: Dict) -> List[Dict]:
        """Scrape a specific document type"""
        records = []
        
        # Navigate to search page
        await page.goto(CLERK_URL, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=LOOKBACK_DAYS)
        
        # Fill in search form
        try:
            # Select document type
            await page.select_option('select[name="ctl00$ContentPlaceHolder1$DocTypesFrom"]', doc_code)
            await asyncio.sleep(1)
            
            # Fill date range
            await page.fill('input[name="ctl00$ContentPlaceHolder1$RecordDateFrom"]', 
                          start_date.strftime('%m/%d/%Y'))
            await page.fill('input[name="ctl00$ContentPlaceHolder1$RecordDateTo"]', 
                          end_date.strftime('%m/%d/%Y'))
            await asyncio.sleep(1)
            
            # Submit search
            await page.click('input[type="submit"][value="Search"]')
            await page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(2)
            
            # Check for results
            content = await page.content()
            
            if 'No results found' in content or 'No records match' in content:
                return records
            
            # Parse results
            soup = BeautifulSoup(content, 'html.parser')
            records = self._parse_results_page(soup, doc_code, doc_info)
            
        except Exception as e:
            print(f"Error during form submission for {doc_code}: {e}")
            # Try to capture page content for debugging
            try:
                content = await page.content()
                # Continue anyway - don't crash
            except:
                pass
        
        return records
    
    def _parse_results_page(self, soup: BeautifulSoup, doc_code: str, doc_info: Dict) -> List[Dict]:
        """Parse the results table"""
        records = []
        
        # Find results table
        table = soup.find('table', {'id': lambda x: x and 'GridView' in x}) or \
                soup.find('table', class_=lambda x: x and 'grid' in x.lower() if x else False)
        
        if not table:
            return records
        
        rows = table.find_all('tr')[1:]  # Skip header
        
        for row in rows:
            try:
                cells = row.find_all('td')
                if len(cells) < 4:
                    continue
                
                # Extract data (adjust indices based on actual table structure)
                doc_num = cells[0].get_text(strip=True) if len(cells) > 0 else ''
                filed_date = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                grantor = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                grantee = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                legal_desc = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                
                # Extract amount
                amount = None
                amount_text = cells[5].get_text(strip=True) if len(cells) > 5 else ''
                amount_match = re.search(r'\$?([\d,]+\.?\d*)', amount_text)
                if amount_match:
                    try:
                        amount = float(amount_match.group(1).replace(',', ''))
                    except:
                        pass
                
                # Build document URL
                doc_url = self._build_doc_url(doc_num, row)
                
                # Enrich with property data
                prop_data = self.property_loader.lookup_owner(grantor)
                
                record = {
                    'doc_num': doc_num,
                    'doc_type': doc_code,
                    'doc_type_name': doc_info['name'],
                    'filed': filed_date,
                    'category': doc_info['category'],
                    'category_label': doc_info['name'],
                    'owner': grantor,
                    'grantee': grantee,
                    'amount': amount,
                    'legal': legal_desc,
                    'clerk_url': doc_url,
                }
                
                # Add property data if found
                if prop_data:
                    record.update({
                        'prop_address': prop_data.get('prop_address'),
                        'prop_city': prop_data.get('prop_city'),
                        'prop_state': prop_data.get('prop_state'),
                        'prop_zip': prop_data.get('prop_zip'),
                        'mail_address': prop_data.get('mail_address'),
                        'mail_city': prop_data.get('mail_city'),
                        'mail_state': prop_data.get('mail_state'),
                        'mail_zip': prop_data.get('mail_zip'),
                    })
                else:
                    record.update({
                        'prop_address': None,
                        'prop_city': None,
                        'prop_state': 'FL',
                        'prop_zip': None,
                        'mail_address': None,
                        'mail_city': None,
                        'mail_state': None,
                        'mail_zip': None,
                    })
                
                # Calculate score and flags
                flags, score = self._calculate_score(record, doc_info)
                record['flags'] = flags
                record['score'] = score
                
                records.append(record)
                
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue
        
        return records
    
    def _build_doc_url(self, doc_num: str, row) -> str:
        """Build direct URL to document"""
        # Try to find link in row
        link = row.find('a')
        if link and link.get('href'):
            href = link['href']
            if href.startswith('http'):
                return href
            return urljoin(CLERK_URL, href)
        
        # Fallback: construct URL
        base = "https://or.duvalclerk.com/search/"
        return f"{base}DocumentView?id={quote(doc_num)}"
    
    def _calculate_score(self, record: Dict, doc_info: Dict) -> Tuple[List[str], int]:
        """Calculate seller motivation score and flags"""
        flags = list(doc_info['flags'])
        score = 30  # Base score
        
        # Add points for each flag
        score += len(flags) * 10
        
        # Check for LP + foreclosure combo
        if record['doc_type'] in ['LP', 'NOFC'] and 'Pre-foreclosure' in flags:
            score += 20
        
        # Amount-based scoring
        if record['amount']:
            if record['amount'] > 100000:
                score += 15
            elif record['amount'] > 50000:
                score += 10
        
        # New this week
        try:
            filed_date = datetime.strptime(record['filed'], '%m/%d/%Y')
            days_ago = (datetime.now() - filed_date).days
            if days_ago <= 7:
                flags.append('New this week')
                score += 5
        except:
            pass
        
        # Has address
        if record.get('prop_address') or record.get('mail_address'):
            score += 5
        
        # LLC/Corp owner
        owner = record['owner'].upper()
        if any(x in owner for x in ['LLC', 'CORP', 'INC', 'LTD', 'COMPANY', 'CO.']):
            flags.append('LLC / corp owner')
            score += 10
        
        # Cap at 100
        score = min(score, 100)
        
        return flags, score


def export_to_ghl_csv(records: List[Dict], output_path: str):
    """Export records to GoHighLevel-compatible CSV"""
    import csv
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'First Name', 'Last Name', 'Mailing Address', 'Mailing City', 
            'Mailing State', 'Mailing Zip', 'Property Address', 'Property City',
            'Property State', 'Property Zip', 'Lead Type', 'Document Type',
            'Date Filed', 'Document Number', 'Amount/Debt Owed', 'Seller Score',
            'Motivated Seller Flags', 'Source', 'Public Records URL'
        ])
        
        for record in records:
            # Parse name
            owner = record['owner']
            first_name, last_name = '', owner
            
            if ',' in owner:
                parts = owner.split(',', 1)
                last_name = parts[0].strip()
                first_name = parts[1].strip() if len(parts) > 1 else ''
            else:
                parts = owner.split(None, 1)
                if len(parts) >= 2:
                    first_name = parts[0]
                    last_name = parts[1]
            
            writer.writerow([
                first_name,
                last_name,
                record.get('mail_address', ''),
                record.get('mail_city', ''),
                record.get('mail_state', ''),
                record.get('mail_zip', ''),
                record.get('prop_address', ''),
                record.get('prop_city', ''),
                record.get('prop_state', 'FL'),
                record.get('prop_zip', ''),
                record['category_label'],
                record['doc_type_name'],
                record['filed'],
                record['doc_num'],
                f"${record['amount']:,.2f}" if record.get('amount') else '',
                record['score'],
                '; '.join(record['flags']),
                'Duval County Clerk',
                record['clerk_url']
            ])
    
    print(f"GHL CSV exported to: {output_path}")


def save_results(records: List[Dict], output_paths: List[str]):
    """Save results to JSON files"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    
    with_address = sum(1 for r in records if r.get('prop_address') or r.get('mail_address'))
    
    output = {
        'fetched_at': datetime.now().isoformat(),
        'source': 'Duval County Clerk of Courts',
        'date_range': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        },
        'total': len(records),
        'with_address': with_address,
        'records': records
    }
    
    for path in output_paths:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(records)} records to: {path}")


async def main():
    """Main execution function"""
    print("=" * 60)
    print("Duval County Motivated Seller Lead Scraper")
    print("=" * 60)
    
    # Load property appraiser data
    print("\n[1/3] Loading property appraiser data...")
    property_loader = PropertyDataLoader()
    property_loader.load_parcel_data()
    
    # Scrape clerk records
    print("\n[2/3] Scraping clerk records...")
    scraper = DuvalClerkScraper(property_loader)
    records = await scraper.scrape_all_doc_types()
    
    # Sort by score (highest first)
    records.sort(key=lambda x: x['score'], reverse=True)
    
    # Save results
    print("\n[3/3] Saving results...")
    save_results(records, [
        'dashboard/records.json',
        'data/records.json'
    ])
    
    # Export GHL CSV
    export_to_ghl_csv(records, 'data/ghl_export.csv')
    
    print("\n" + "=" * 60)
    print(f"✓ Scrape complete! Found {len(records)} total leads")
    print(f"✓ Top score: {records[0]['score'] if records else 0}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
