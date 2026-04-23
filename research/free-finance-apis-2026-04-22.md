# Free APIs for Structured Finance & US Macro Podcast

_Research date: 2026-04-22 • Depth: medium • Search: Tavily_

## TL;DR

For a free-tier podcast on US macro trends and structured finance, **Finnhub (real-time stocks)** + **FRED API (economic data)** + **StockData (news)** cover 80% of needs. Add **Treasury API** for bond/fiscal data and **Alpha Vantage** for forex/indicators. Structured finance data (credit spreads, securitized products) requires either free-tier limitations or paid alternatives. [^1][^2][^3][^4]

---

## Key Findings

- **FRED API**: Free, 800,000+ economic time series, no rate limits explicitly stated, managed by Federal Reserve [^2]
- **Finnhub Free Tier**: 60 API calls/minute, real-time stocks/forex/crypto, 1+ year company news, 30+ years fundamentals [^1][^5]
- **StockData.org**: 100 daily API calls free, real-time US stock prices + news, 7+ years intraday historical [^6]
- **Alpha Vantage**: Free tier, stocks/forex/crypto/technical indicators, ~5 API calls/minute limit [^7]
- **Financial Modeling Prep (FMP)**: Free tier includes stocks, indices, economic indicators, treasury rates [^8]
- **US Treasury API**: 100% free government fiscal data (spending, revenue, debt, bond prices) [^9]
- **Office of Financial Research (OFR)**: Free credit spreads API, includes high-yield bond spreads [^10]
- **Structured Finance**: No fully free APIs; professional tools (Moody's, Bloomberg) are paid; workaround: use FRED spreads + manual research [^11]

---

## Detailed Breakdown

### 1. Real-Time Stock Market Data

#### **Finnhub** (Recommended) [^1][^5]
- **Tier**: FREE (60 API calls/minute)
- **Coverage**: 60+ global stock exchanges, forex, 15+ crypto exchanges
- **Data**: Real-time quotes, 30+ years historical, company news (1+ year free tier), insider trades, earnings transcripts
- **Best For**: Stocks, forex, international markets
- **Limitations**: 60 calls/min (throttles at peak); fundamental data limited on free tier
- **Integration**: REST API, WebSocket for real-time, Python/JavaScript SDKs
- **Registration**: Free API key at finnhub.io

#### **Alpha Vantage** [^7]
- **Tier**: FREE (with rate limit ~5 calls/min)
- **Coverage**: US + global stocks, forex, crypto, technical indicators (60+)
- **Data**: Real-time, historical, intraday (1-min, 5-min, 15-min intervals), earnings surprises
- **Best For**: Technical analysis, indicators, forex
- **Limitations**: Slower (120ms latency on free), rate-limited, delays on premium features
- **Integration**: REST API, JSON, supports spreadsheets
- **Registration**: Free API key at alphavantage.co

#### **StockData.org** [^6]
- **Tier**: FREE (100 API calls/day)
- **Coverage**: US stocks, indices, ETFs, crypto, forex
- **Data**: Real-time + 7+ years intraday historical, market news from 5,000+ sources
- **Best For**: US market focus, news integration, extended hours data
- **Limitations**: Daily cap (100 calls); international data is EOD only
- **Integration**: REST API, JSON response
- **Registration**: Free at stockdata.org

### 2. Economic Indicators & Macro Data (BEST FREE OPTION)

#### **FRED API** (Federal Reserve Economic Data) [^2]
- **Tier**: Completely FREE, no rate limits disclosed
- **Coverage**: 800,000+ time series from 118+ sources
- **Data**: GDP, unemployment, inflation, interest rates, trade, housing, consumer spending, FOMC meeting data
- **Frequency**: Annual, quarterly, monthly, weekly, daily
- **Historical Depth**: 30+ years for most series
- **Best For**: Macro podcast backbone—this is the gold standard for US economic data
- **Integration**: REST API (v1 & v2), Excel Add-in, Python packages (e.g., `fredapi`), JSON/XML
- **Registration**: Free account + API key at fred.stlouisfed.org
- **Sample Series IDs**: GDP, UNRATE, CPIAUCSL, FEDFUNDS, DGS10 (10-year Treasury yield)
- **Podcast Application**: Release calendar shows when new data drops (useful for episode timing)

#### **Financial Modeling Prep (FMP) - Economics** [^8]
- **Tier**: FREE with basic plan
- **Coverage**: Treasury rates (all maturities), economic indicators (GDP, inflation, unemployment), economic calendar
- **Data**: Real-time updates, historical depth varies
- **Best For**: Treasury curve data, economic calendar for planning podcast episodes
- **Integration**: REST API
- **Registration**: Free at site.financialmodelingprep.com

### 3. Financial News for Podcast Scripts

#### **StockData.org News API** [^6]
- **Tier**: FREE (part of 100 daily API calls)
- **Coverage**: 5,000+ news sources in 30+ languages
- **Data**: Real-time news with ticker/crypto tags, sentiment analysis, historical news
- **Best For**: Podcast story sourcing, market context
- **Limitations**: Free tier has daily request limit

#### **Finnhub Company News** [^1]
- **Tier**: FREE (60 calls/min total)
- **Coverage**: North American companies, 1+ year historical
- **Data**: Headlines, summaries, source URLs, publishing time
- **Best For**: Company-specific context for macro stories
- **Limitation**: 1 year lookback on free tier (paid gets 20 years)

### 4. Bond & Structured Finance Data

#### **US Treasury API** [^9]
- **Tier**: Completely FREE
- **Coverage**: Treasury bond prices, yields, savings bonds, debt statistics
- **Data**: Daily updates, historical prices/yields by maturity
- **Best For**: Government bond yields, Treasury curve for macro analysis
- **Endpoint Example**: `/v2/accounting/od/debt_to_penny` (daily debt data)
- **Registration**: Free at fiscaldata.treasury.gov

#### **Office of Financial Research (OFR) - Credit Spreads API** [^10]
- **Tier**: FREE
- **Coverage**: High-yield bond spreads, ICE BofA indices (available via FRED)
- **Data**: OAS (Option-Adjusted Spread) for HY bonds, corporate spreads
- **Best For**: Credit cycle analysis, structured finance context
- **Via FRED**: Series like BAMLH0A0HYM2 (ICE BofA High Yield OAS)
- **Registration**: Access via FRED (same account)

#### **Moody's Structured Finance API** [^11]
- **Tier**: PAID (no free tier)
- **Coverage**: Cash flow models, credit models, deal libraries for RMBS, ABS, CMBS, CDOs
- **Limitation**: Enterprise-only, $$$
- **Workaround**: Use FRED + manual structured finance research, SEC filings (via Marketstack free tier)

### 5. SEC Filings & Corporate Data

#### **Marketstack (with EDGAR)** [^12]
- **Tier**: FREE (100 monthly API requests)
- **Coverage**: 30,000+ tickers, EOD historical data, 10-K/10-Q/8-K filings
- **Data**: 15+ years historical, EDGAR document access
- **Best For**: Occasional CEO commentary research, fundamental company info
- **Limitation**: 100 req/month is tight; mainly useful for ad-hoc lookups
- **Registration**: Free at marketstack.com

---

## Recommended Stack for Podcast

| Use Case | API | Free Tier | Why |
|----------|-----|-----------|-----|
| **Macro trends & economic releases** | FRED | Unlimited | 800K time series, no rate limits, Fed-backed |
| **Real-time stock commentary** | Finnhub | 60 calls/min | Global coverage, news included, fast |
| **Breaking market news** | StockData | 100/day | Wide news coverage, sentiment data |
| **Treasury/bond yields** | US Treasury API | Unlimited | Official data, no intermediaries |
| **Credit spreads (HY market)** | FRED (via OFR series) | Unlimited | Available within FRED, macro context |
| **Technical indicators** | Alpha Vantage | Free | 60+ indicators for technical analysis |
| **Corporate fundamentals** | FMP (if needed) | Free tier | Quick balance sheets, limited depth |
| **SEC filings (rare)** | Marketstack EDGAR | 100/month | Backup for deep dives |

---

## Podcast Content Workflow Example

**Episode on "Fed Tightening & Credit Market Stress":**

1. **Lead data** (FRED): Pull latest UNRATE, CPIAUCSL, FEDFUNDS, GDP growth
2. **Bond context** (Treasury API): Current 10Y yield, 2-10 spread
3. **Credit risk** (FRED OFR series): HY spreads (BAMLH0A0HYM2) widening/tightening signal
4. **Breaking news** (Finnhub + StockData): Recent bank earnings misses, credit events
5. **Script sourcing** (Finnhub news): Related company announcements, macro commentary

**Cost**: $0 if you stay within free tier limits.

---

## Disagreements & Limitations

- **Structured Finance Data**: Moody's and Bloomberg dominate; free data is sparse. [^11] Consider supplementing free APIs with manual SEC filing research or public bond price data (TRACE on FINRA).
- **Real-Time vs Delayed**: Finnhub free tier delivers real-time for stocks; bonds are mostly delayed (15min LSE, EOD international). [^1]
- **Rate Limits**: Finnhub's 60 calls/min is adequate for daily podcast research but tight for real-time dashboard apps. For heavier use, upgrade to paid tier.
- **News Quality**: StockData aggregates from 5,000+ sources; quality varies. Finnhub news is cleaner but 1-year depth on free tier. [^1][^6]

---

## Getting Started

### Step 1: Register for Free API Keys
- **FRED**: fred.stlouisfed.org → Register → API Keys
- **Finnhub**: finnhub.io → Get free API key
- **StockData**: stockdata.org → Sign up (no credit card)
- **Alpha Vantage**: alphavantage.co → Support → API Key
- **FMP**: site.financialmodelingprep.com → Create account

### Step 2: Test in Python

```python
# FRED Example
import requests

FRED_API_KEY = "your_key_here"
url = f"https://api.stlouisfed.org/fred/series/observations?series_id=UNRATE&api_key={FRED_API_KEY}&file_type=json"
response = requests.get(url)
print(response.json())

# Finnhub Example
import finnhub
finnhub_client = finnhub.Client(api_key="your_key_here")
quotes = finnhub_client.quote("AAPL")
```

### Step 3: Combine into Podcast Pipeline
- Scheduled pulls: Daily FRED/Treasury updates (morning)
- Manual: Ad-hoc news pulls from Finnhub/StockData before recording
- Archive: Save weekly snapshots for trend references in scripts

---

## Sources

[^1]: Finnhub Stock APIs (2026) — https://finnhub.io/ (accessed 2026-04-22)
[^2]: St. Louis Fed FRED API Documentation — https://fred.stlouisfed.org/docs/api/fred/ (accessed 2026-04-22)
[^3]: Alpha Vantage Stock APIs — https://www.alphavantage.co/ (accessed 2026-04-22)
[^4]: Marketstack Free Stock API — https://marketstack.com/ (accessed 2026-04-22)
[^5]: Finnhub Pricing & Free Tier — https://finnhub.io/pricing (accessed 2026-04-22)
[^6]: StockData.org Free API — https://www.stockdata.org/ (accessed 2026-04-22)
[^7]: Alpha Vantage Documentation — https://www.alphavantage.co/documentation/ (accessed 2026-04-22)
[^8]: Financial Modeling Prep (FMP) — https://site.financialmodelingprep.com/developer/docs (accessed 2026-04-22)
[^9]: US Treasury Fiscal Data API — https://fiscaldata.treasury.gov/api-documentation/ (accessed 2026-04-22)
[^10]: Office of Financial Research (OFR) Spreads API — https://www.financialresearch.gov/short-term-funding-monitor/ (accessed 2026-04-22)
[^11]: Moody's Structured Finance API (Enterprise/Paid) — https://www.moodys.com/web/en/us/site-assets/apis-2024.pdf (accessed 2026-04-22)
[^12]: Marketstack EDGAR Filings — https://marketstack.com/ (accessed 2026-04-22)