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

## Setup

### 1. Get your Kit API key

1. Go to [Kit Developer Settings](https://app.kit.com/account_settings/developer_settings)
2. Click "Add a new key"
3. Copy the key immediately (it won't be shown again)

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your API key

Copy the example env file and add your key:

```bash
cp .env.example .env
```

Edit `.env` and replace `your_api_key_here` with your actual API key.

Alternatively, pass it directly:

```bash
python main.py --api-key YOUR_KEY
```

## Usage

```bash
# Full analysis with default settings
python main.py

# Show top/bottom 10 broadcasts instead of 5
python main.py --top 10

# Export report to a text file
python main.py --export report.txt

# Use a specific API key
python main.py --api-key sk_xxx
```

## Project Structure

```
├── main.py          # CLI entry point
├── kit_client.py    # Kit.com API v4 client
├── analyzer.py      # Performance analysis and recommendations engine
├── report.py        # Rich terminal report formatting
├── config.py        # Configuration and benchmark constants
├── requirements.txt # Python dependencies
├── .env.example     # Template for API key configuration
└── .gitignore
```

## API Rate Limits

The Kit API allows 120 requests per 60-second rolling window with API key auth. The tool handles pagination and rate limiting automatically. For accounts with many broadcasts, the initial fetch may require multiple API calls (one per broadcast for stats + clicks).
