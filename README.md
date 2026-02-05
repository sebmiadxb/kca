# Kit.com Email Performance Analyzer

Fetches your email broadcast data from [Kit.com](https://kit.com) (formerly ConvertKit), analyzes performance metrics, and generates a detailed report with actionable optimization recommendations.

## What It Analyzes

- **Open Rate** — overall, per-broadcast, and trends over time
- **Click Rate** — overall, per-broadcast, and per-link breakdown
- **Click-to-Open Rate** — how well email content drives clicks after opens
- **Unsubscribe Rate** — list health monitoring
- **Subject Line Patterns** — which styles (short/long, questions, personalization, emoji) perform best
- **Send Time Analysis** — best day-of-week and hour-of-day for engagement
- **Performance Trends** — whether your metrics are improving or declining
- **Industry Benchmarks** — how you compare to creator/newsletter averages
- **Top Links** — which URLs get the most clicks across all broadcasts

## Deploy to a Live Website (Render — free)

The easiest way to get this running. No coding or terminal required.

### 1. Get your Kit API key

1. Go to [Kit Developer Settings](https://app.kit.com/account_settings/developer_settings)
2. Click **"Add a new key"**
3. Copy the key immediately (it won't be shown again)

### 2. Deploy to Render

1. Create a free account at [render.com](https://render.com)
2. Click **New > Web Service**
3. Connect your GitHub account and select this repository
4. Render auto-detects the settings — just click **Create Web Service**
5. Wait for the build to finish (a few minutes)
6. You'll get a URL like `https://email-performance-analyzer-xxxx.onrender.com`
7. Open that URL, paste your Kit API key, and click **Analyze My Emails**

That's it. Bookmark the URL and use it whenever you want.

## Alternative: Run Locally

If you prefer running it on your own computer:

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000 in your browser.

### Command Line (advanced)

```bash
python main.py                    # Full analysis
python main.py --top 10           # Show top/bottom 10
python main.py --export report.txt  # Save to file
python main.py --api-key sk_xxx   # Pass key directly
```

## Project Structure

```
├── app.py           # Web app
├── main.py          # CLI (terminal alternative)
├── kit_client.py    # Kit.com API v4 client
├── analyzer.py      # Performance analysis + recommendations engine
├── report.py        # Terminal report formatting
├── config.py        # Configuration and benchmark constants
├── templates/
│   ├── index.html   # Landing page
│   └── report.html  # Report page
├── render.yaml      # Render deployment config
├── Procfile         # Process config for hosting
├── requirements.txt # Python dependencies
├── .env.example     # API key template (local use)
└── .gitignore
```

## API Rate Limits

The Kit API allows 120 requests per 60-second rolling window with API key auth. The tool handles pagination and rate limiting automatically. For accounts with many broadcasts, the initial fetch may require multiple API calls (one per broadcast for stats + clicks).
