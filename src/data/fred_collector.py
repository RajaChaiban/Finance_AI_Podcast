import httpx
from src.data.models import MacroIndicator
from src.utils.logger import log
from src.utils.retry import retry_http

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# Series to fetch: id -> (display name, unit)
SERIES = {
    "DGS10": ("10-Year Treasury Yield", "percent"),
    "DGS2": ("2-Year Treasury Yield", "percent"),
    "FEDFUNDS": ("Federal Funds Rate", "percent"),
    "UNRATE": ("Unemployment Rate", "percent"),
    "T10Y2Y": ("10Y-2Y Yield Spread", "percent"),
}


class FredCollector:
    def __init__(self, api_key: str, client: httpx.Client | None = None):
        self.api_key = api_key
        self.client = client

    def collect_all(self) -> dict:
        log.info("Collecting data from FRED...")
        indicators = []
        for series_id, (name, unit) in SERIES.items():
            indicator = self._get_series(series_id, name, unit)
            if indicator:
                indicators.append(indicator)
        log.info(f"FRED collection complete: {len(indicators)} indicators")
        return {"macro_indicators": indicators}

    @retry_http(attempts=2)
    def _fetch_series(self, series_id: str) -> dict:
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 2,
        }
        if self.client is not None:
            resp = self.client.get(BASE_URL, params=params)
        else:
            with httpx.Client(timeout=30) as client:
                resp = client.get(BASE_URL, params=params)
        resp.raise_for_status()
        return resp.json()

    def _get_series(self, series_id: str, name: str, unit: str) -> MacroIndicator | None:
        try:
            data = self._fetch_series(series_id)
            observations = data.get("observations", [])
            if not observations:
                log.warning(f"FRED: no observations for {series_id}")
                return None

            latest = observations[0]
            value = latest.get("value", ".")
            if value == ".":  # FRED uses "." for missing values
                return None

            previous_value = 0.0
            if len(observations) > 1:
                prev = observations[1].get("value", ".")
                if prev != ".":
                    previous_value = float(prev)

            return MacroIndicator(
                name=name,
                series_id=series_id,
                value=float(value),
                previous_value=previous_value,
                date=latest.get("date", ""),
                unit=unit,
            )
        except Exception as e:
            log.warning(f"Failed to fetch FRED series {series_id}: {e}")
            return None
