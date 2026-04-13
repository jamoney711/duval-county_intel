# Duval County Motivated Seller Lead Scraper

**Automated daily scraping of motivated seller leads from Duval County, Florida public records.**

## 🎯 What This Does

This system automatically scrapes the Duval County Clerk of Courts portal every day to find motivated seller leads, enriches them with property appraiser data, scores them, and presents them in a beautiful dashboard.

### Lead Types Collected

- **LP** - Lis Pendens (Pre-foreclosure)
- **NOFC** - Notice of Foreclosure  
- **TAXDEED** - Tax Deed
- **JUD/CCJ/DRJUD** - Judgments
- **LNCORPTX/LNIRS/LNFED** - Tax Liens
- **LN/LNMECH/LNHOA** - Various Liens
- **MEDLN** - Medicaid Lien
- **PRO** - Probate Documents
- **NOC** - Notice of Commencement
- **RELLP** - Release Lis Pendens

## 🚀 Features

✅ **Automated Daily Scraping** - Runs every day at 7 AM UTC via GitHub Actions  
✅ **Property Enrichment** - Matches clerk records with property appraiser data for addresses  
✅ **Smart Scoring** - Scores leads 0-100 based on multiple motivation factors  
✅ **Beautiful Dashboard** - Interactive web interface to browse and filter leads  
✅ **GHL Export** - CSV export ready for GoHighLevel import  
✅ **Never Crashes** - Built with retry logic and error handling  
✅ **Zero Cost** - Runs entirely on GitHub (free tier)

## 📊 Scoring Algorithm

**Base Score:** 30 points  
**Bonuses:**
- +10 per motivation flag
- +20 for Lis Pendens + Foreclosure combo
- +15 for amount > $100,000
- +10 for amount > $50,000
- +5 for new this week
- +5 for has address
- +10 for LLC/Corp owner

**Motivation Flags:**
- Lis pendens
- Pre-foreclosure
- Judgment lien
- Tax lien
- Mechanic lien
- Probate / estate
- LLC / corp owner
- New this week

## 🛠️ Setup Instructions

### 1. Fork This Repository

Click the "Fork" button at the top right of this repository.

### 2. Enable GitHub Actions

1. Go to your forked repository
2. Click "Actions" tab
3. Click "I understand my workflows, go ahead and enable them"

### 3. Enable GitHub Pages

1. Go to Settings → Pages
2. Source: "GitHub Actions"
3. Save

### 4. Run First Scrape

1. Go to Actions → "Duval County Lead Scraper"
2. Click "Run workflow"
3. Wait 5-10 minutes for completion

### 5. View Dashboard

Your dashboard will be available at:
```
https://[your-username].github.io/[repo-name]/
```

## 📁 File Structure

```
├── scraper/
│   ├── fetch.py           # Main scraper script
│   └── requirements.txt   # Python dependencies
├── dashboard/
│   ├── index.html         # Dashboard interface
│   └── records.json       # Lead data (auto-updated)
├── data/
│   ├── records.json       # Lead data backup
│   └── ghl_export.csv     # GoHighLevel CSV export
└── .github/
    └── workflows/
        └── scrape.yml     # GitHub Actions automation
```

## 🔧 Configuration

Edit `scraper/fetch.py` to customize:

```python
LOOKBACK_DAYS = 14        # How many days back to search
MAX_RETRIES = 3          # Retry attempts per document type
RETRY_DELAY = 2          # Seconds between retries
```

Modify scoring in `_calculate_score()` method.

## 📥 GoHighLevel Import

After each scrape, a GHL-ready CSV is created at `data/ghl_export.csv`:

**Columns:**
- First Name, Last Name
- Mailing Address, City, State, Zip
- Property Address, City, State, Zip
- Lead Type, Document Type, Date Filed
- Document Number, Amount/Debt Owed
- Seller Score, Motivated Seller Flags
- Source, Public Records URL

**To Import:**
1. Download `ghl_export.csv` from your repository
2. In GoHighLevel: Contacts → Import
3. Map the CSV columns
4. Import!

## 🎨 Dashboard Features

- **Search** - Filter by owner, address, document number
- **Category Filter** - Foreclosure, Liens, Judgments, Probate, Tax
- **Score Filter** - Only show high-scoring leads (50+, 70+, 80+, 90+)
- **Direct Links** - View original clerk records
- **Google Maps** - Quick property location lookup
- **Responsive** - Works on mobile, tablet, desktop

## 🔄 How It Works

### Daily Workflow

1. **7 AM UTC** - GitHub Actions triggers
2. **Property Data** - Attempts to download Duval County parcel DBF
3. **Clerk Scraping** - Playwright visits clerk portal, searches each document type
4. **Data Enrichment** - Matches owner names to get property/mailing addresses
5. **Scoring** - Calculates motivation score for each lead
6. **Export** - Saves JSON and CSV files
7. **Commit** - Pushes updated data to repository
8. **Deploy** - Updates GitHub Pages dashboard

### Property Appraiser Integration

The scraper attempts to find and download the Duval County Property Appraiser bulk parcel data (DBF format). It creates owner lookup variants:

- "FIRST LAST"
- "LAST, FIRST"  
- "LAST FIRST"

This allows matching clerk records (which may use any format) to parcel data for address enrichment.

**If property data is unavailable:**  
The scraper still runs successfully but leads won't have property/mailing addresses.

## ⚠️ Important Notes

### Rate Limiting
The clerk portal may rate-limit requests. The scraper includes:
- 2-second delays between document types
- 3 retry attempts with backoff
- User agent rotation

### Data Accuracy
- Data comes from public records (clerk & property appraiser)
- Some leads may have incomplete information
- Addresses depend on successful owner name matching
- Always verify critical details directly

### Legal Compliance
- All data is from public records
- Follow fair housing laws when using leads
- Respect TCPA/DNC regulations
- This is for legitimate business use only

## 🐛 Troubleshooting

### Scraper Fails
Check Actions logs for errors. Common issues:
- Clerk website changed structure → Update selectors
- Property appraiser URL changed → Update URL patterns
- Playwright timeout → Increase wait times

### No Addresses
- Property appraiser data download failed
- Owner name format mismatch
- Run manual test: `python scraper/fetch.py`

### Dashboard Not Updating
- Check Actions tab for failed runs
- Ensure GitHub Pages is enabled
- Clear browser cache

## 🚀 Advanced Usage

### Run Locally

```bash
# Install dependencies
pip install -r scraper/requirements.txt
python -m playwright install chromium

# Run scraper
python scraper/fetch.py

# Results saved to:
# - dashboard/records.json
# - data/records.json  
# - data/ghl_export.csv
```

### Change Schedule

Edit `.github/workflows/scrape.yml`:

```yaml
on:
  schedule:
    - cron: '0 7 * * *'  # Daily at 7 AM UTC
    # Examples:
    # '0 */6 * * *'      # Every 6 hours
    # '0 9 * * 1,3,5'    # Mon/Wed/Fri at 9 AM
```

### Add More Counties

Copy scraper structure and modify:
- `CLERK_URL` - New county clerk portal
- `DOC_TYPES` - County-specific document codes
- Property appraiser URLs
- Update parser selectors for new HTML structure

## 📈 Optimization Tips

1. **Focus on High Scores** - Filter for 70+ scores in dashboard
2. **New Leads First** - Sort by filed date, contact within 48 hours
3. **Multiple Flags** - Leads with 3+ flags are usually highly motivated
4. **LP + NOFC Combo** - These are pre-foreclosure, very hot leads
5. **Corporate Owners** - Often easier to negotiate with

## 🤝 Contributing

Found a bug? Have an idea? 

1. Open an issue
2. Submit a pull request
3. Star the repo if it helps you!

## 📄 License

MIT License - Use freely for your real estate business

## ⚖️ Disclaimer

This software is provided as-is. The authors are not responsible for:
- Accuracy of scraped data
- Compliance with local laws/regulations  
- Business decisions made using this data
- Website changes breaking the scraper

Always verify information and consult legal counsel for compliance questions.

---

**Made with ❤️ for real estate investors and wholesalers**

*Happy lead hunting! 🏠💰*
