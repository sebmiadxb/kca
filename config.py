import os
from dotenv import load_dotenv

load_dotenv()

KIT_API_KEY = os.getenv("KIT_API_KEY", "")
KIT_API_BASE = "https://api.kit.com/v4"

# Industry benchmark averages for email marketing (creator/newsletter segment)
BENCHMARKS = {
    "open_rate": 0.35,         # 35% average open rate for creators
    "click_rate": 0.025,       # 2.5% average click rate
    "click_to_open_rate": 0.07, # 7% average click-to-open rate
    "unsubscribe_rate": 0.003,  # 0.3% average unsubscribe rate
}
