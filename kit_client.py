"""Kit.com (ConvertKit) API v4 client for fetching broadcast/email data."""

import time
import requests
from config import KIT_API_KEY, KIT_API_BASE


class KitAPIError(Exception):
    """Raised when a Kit API request fails."""

    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Kit API error {status_code}: {message}")


class KitClient:
    """Client for the Kit.com API v4."""

    def __init__(self, api_key=None):
        self.api_key = api_key or KIT_API_KEY
        if not self.api_key:
            raise ValueError(
                "Kit API key is required. Set KIT_API_KEY in your .env file.\n"
                "Get yours at: https://app.kit.com/account_settings/developer_settings"
            )
        self.session = requests.Session()
        self.session.headers.update({"X-Kit-Api-Key": self.api_key})
        self._request_count = 0

    def _request(self, method, path, params=None, max_retries=6):
        """Make an API request with retry logic and rate-limit handling."""
        url = f"{KIT_API_BASE}{path}"

        # Pace requests: pause every 100 calls to stay within the
        # 120 requests / 60 seconds rolling window.
        self._request_count += 1
        if self._request_count % 100 == 0:
            time.sleep(60)

        for attempt in range(max_retries + 1):
            try:
                resp = self.session.request(method, url, params=params, timeout=30)
            except requests.RequestException as exc:
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                raise KitAPIError(0, f"Network error: {exc}") from exc

            if resp.status_code == 429:
                # Rate limited — wait and retry with increasing backoff
                retry_after = int(resp.headers.get("Retry-After", 0))
                wait = max(retry_after, 2 ** attempt, 10)
                if attempt < max_retries:
                    time.sleep(wait)
                    continue
                raise KitAPIError(429, "Rate limited. Try again later.")

            if resp.status_code >= 400:
                try:
                    body = resp.json()
                    msg = body.get("errors", [resp.text])
                except Exception:
                    msg = resp.text
                raise KitAPIError(resp.status_code, str(msg))

            return resp.json()

        raise KitAPIError(0, "Max retries exceeded")

    # ------------------------------------------------------------------ #
    # Broadcasts
    # ------------------------------------------------------------------ #

    def list_broadcasts(self, per_page=500):
        """Fetch all broadcasts, handling cursor-based pagination.

        Returns a list of broadcast dicts.
        """
        broadcasts = []
        params = {"per_page": per_page, "include_total_count": "true"}
        while True:
            data = self._request("GET", "/broadcasts", params=params)
            broadcasts.extend(data.get("broadcasts", []))
            pagination = data.get("pagination", {})
            if pagination.get("has_next_page") and pagination.get("end_cursor"):
                params["after"] = pagination["end_cursor"]
            else:
                break
        return broadcasts

    def get_broadcast_stats(self, broadcast_id):
        """Get performance stats for a single broadcast.

        Returns the broadcast dict with nested ``stats`` object containing:
        recipients, open_rate, emails_opened, click_rate, unsubscribe_rate,
        unsubscribes, total_clicks, status, progress, etc.
        """
        data = self._request("GET", f"/broadcasts/{broadcast_id}/stats")
        return data.get("broadcast", {})

    def get_broadcast_clicks(self, broadcast_id):
        """Get per-link click data for a broadcast.

        Returns a list of click dicts with url, unique_clicks,
        click_to_delivery_rate, click_to_open_rate.
        """
        clicks = []
        params = {}
        while True:
            data = self._request(
                "GET", f"/broadcasts/{broadcast_id}/clicks", params=params
            )
            broadcast = data.get("broadcast", {})
            clicks.extend(broadcast.get("clicks", []))
            pagination = data.get("pagination", {})
            if pagination.get("has_next_page") and pagination.get("end_cursor"):
                params["after"] = pagination["end_cursor"]
            else:
                break
        return clicks

    def get_all_broadcast_data(self):
        """Fetch every broadcast together with its stats and click data.

        Returns a list of enriched broadcast dicts, each containing:
        - All fields from the broadcast listing
        - ``stats``: performance stats dict
        - ``clicks``: list of per-link click dicts
        """
        broadcasts = self.list_broadcasts()
        enriched = []
        for bc in broadcasts:
            bid = bc["id"]
            # Fetch stats
            stats_data = self.get_broadcast_stats(bid)
            bc["stats"] = stats_data.get("stats", {})
            # Fetch click details
            bc["clicks"] = self.get_broadcast_clicks(bid)
            enriched.append(bc)
            # Small delay between broadcasts to respect rate limits
            time.sleep(0.6)
        return enriched
