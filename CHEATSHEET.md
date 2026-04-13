# Quick Reference Cheat Sheet

## 🚀 Instant Deploy to GitHub

```bash
# 1. Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit: Duval County lead scraper"

# 2. Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main

# 3. Enable in GitHub:
#    - Actions: Click "I understand my workflows"
#    - Pages: Settings → Pages → Source: GitHub Actions
#    - Run: Actions → "Duval County Lead Scraper" → Run workflow

# 4. Dashboard URL:
#    https://YOUR_USERNAME.github.io/YOUR_REPO/
```

## 💻 Local Development

```bash
# Quick setup
./setup.sh

# Or manual:
pip install -r scraper/requirements.txt
python -m playwright install chromium

# Run scraper
python scraper/fetch.py

# View results
open dashboard/index.html  # Mac
xdg-open dashboard/index.html  # Linux
start dashboard/index.html  # Windows
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `scraper/fetch.py` | Main scraper logic |
| `scraper/requirements.txt` | Python dependencies |
| `dashboard/index.html` | Interactive dashboard |
| `dashboard/records.json` | Lead data (auto-updated) |
| `data/ghl_export.csv` | GoHighLevel import file |
| `.github/workflows/scrape.yml` | Automation config |

## ⚙️ Configuration

**Change Lookback Days:**
```python
# In scraper/fetch.py
LOOKBACK_DAYS = 14  # Change to 7, 30, etc.
```

**Change Schedule:**
```yaml
# In .github/workflows/scrape.yml
schedule:
  - cron: '0 7 * * *'  # Daily 7 AM UTC
  # Examples:
  # '0 */6 * * *'  # Every 6 hours
  # '0 9 * * 1'    # Mondays at 9 AM
```

**Modify Scoring:**
```python
# In scraper/fetch.py → _calculate_score()
score = 30  # Base score
score += 20  # LP+FC combo
score += 15  # Amount > $100k
# etc.
```

## 📊 Document Type Codes

```python
LP      - Lis Pendens
NOFC    - Notice of Foreclosure
TAXDEED - Tax Deed
JUD     - Judgment
CCJ     - Certified Judgment
DRJUD   - Domestic Judgment
LNCORPTX- Corporate Tax Lien
LNIRS   - IRS Lien
LNFED   - Federal Lien
LN      - Lien
LNMECH  - Mechanic Lien
LNHOA   - HOA Lien
MEDLN   - Medicaid Lien
PRO     - Probate
NOC     - Notice of Commencement
RELLP   - Release Lis Pendens
```

## 🔍 Dashboard Filters

- **Search**: Owner, address, doc number
- **Category**: Foreclosure, Lien, Judgment, Probate, Tax
- **Min Score**: 0, 50, 70, 80, 90

## 📥 GHL Import Fields

```
First Name, Last Name
Mailing Address, City, State, Zip
Property Address, City, State, Zip
Lead Type, Document Type, Date Filed
Document Number, Amount/Debt Owed
Seller Score, Motivated Seller Flags
Source, Public Records URL
```

## 🐛 Common Issues

**Scraper fails:**
```bash
# Check logs
cd .github/workflows/
cat scrape.yml

# Test locally
python scraper/fetch.py
```

**No addresses:**
- Property appraiser data not downloaded
- Check logs for DBF download errors
- May need to update property appraiser URLs

**Dashboard not updating:**
- Check Actions tab for failures
- Ensure Pages is enabled
- Clear browser cache (Cmd+Shift+R / Ctrl+Shift+R)

## 🎯 Lead Quality Tips

**Hot Leads (Score 80+):**
- Multiple flags (3+)
- LP + NOFC combo
- Filed within 7 days
- Amount > $100k

**Contact Priority:**
1. New this week + Pre-foreclosure
2. Multiple liens + Has address
3. Probate + LLC owner
4. Tax deed + High amount

**Best Practice:**
- Contact within 48 hours of filing
- Focus on scores 70+
- Cross-reference with county records
- Verify property status before contact

## 📞 Support

- Issues: https://github.com/YOUR_USERNAME/YOUR_REPO/issues
- Docs: README.md
- Test: `python test_setup.py`

## 📈 Scaling Up

**Add More Counties:**
1. Copy `scraper/fetch.py`
2. Update `CLERK_URL`
3. Modify `DOC_TYPES` for county
4. Update HTML selectors
5. Test locally first

**Increase Frequency:**
```yaml
# Run every 6 hours
schedule:
  - cron: '0 */6 * * *'
```

**Export to Multiple CRMs:**
- Add export functions to `scraper/fetch.py`
- Format data for Podio, REsimpli, etc.
- Save to `data/` directory

---

**Pro Tip:** Star this repo! Updates and improvements coming regularly.
