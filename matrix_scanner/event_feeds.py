"""
Event feeds for macro releases, company news, and filings.
All sources are free or use optional API keys.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

import requests

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
YAHOO_RSS_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline"


def get_alpha_vantage_key() -> Optional[str]:
    return os.getenv("ALPHAVANTAGE_API_KEY")


def get_sec_user_agent() -> str:
    return os.getenv("SEC_USER_AGENT", "Corexia/1.0 (contact@example.com)")


def _parse_av_timestamp(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%S")
    except ValueError:
        return None


def fetch_alpha_vantage_news(ticker: str, api_key: str, limit: int = 20) -> List[Dict]:
    if not api_key:
        return []

    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "apikey": api_key,
        "sort": "LATEST",
    }
    response = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=15)
    if response.status_code != 200:
        return []
    data = response.json()
    feed = data.get("feed", [])

    events = []
    for item in feed[:limit]:
        ts = _parse_av_timestamp(item.get("time_published", ""))
        events.append({
            "timestamp": ts,
            "title": item.get("title"),
            "source": item.get("source"),
            "url": item.get("url"),
            "summary": item.get("summary"),
            "event_type": "company_news",
        })
    return events


def fetch_alpha_vantage_market_news(api_key: str, limit: int = 20) -> List[Dict]:
    if not api_key:
        return []

    params = {
        "function": "NEWS_SENTIMENT",
        "topics": "financial_markets,economy_fiscal,economy_monetary",
        "apikey": api_key,
        "sort": "LATEST",
    }
    response = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=15)
    if response.status_code != 200:
        return []
    data = response.json()
    feed = data.get("feed", [])

    events = []
    for item in feed[:limit]:
        ts = _parse_av_timestamp(item.get("time_published", ""))
        events.append({
            "timestamp": ts,
            "title": item.get("title"),
            "source": item.get("source"),
            "url": item.get("url"),
            "summary": item.get("summary"),
            "event_type": "market_news",
        })
    return events


def fetch_alpha_vantage_macro(api_key: str) -> List[Dict]:
    if not api_key:
        return []

    series = [
        ("CPI", "CPI"),
        ("REAL_GDP", "Real GDP"),
        ("UNEMPLOYMENT", "Unemployment"),
        ("FEDERAL_FUNDS_RATE", "Fed Funds Rate"),
        ("INFLATION", "Inflation"),
    ]

    events = []
    for function, label in series:
        params = {"function": function, "apikey": api_key}
        response = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=15)
        if response.status_code != 200:
            continue
        data = response.json()
        points = data.get("data", [])
        if not points:
            continue
        latest = points[0]
        events.append({
            "timestamp": _parse_date(latest.get("date")),
            "title": f"{label} latest release",
            "source": "Alpha Vantage",
            "value": latest.get("value"),
            "event_type": "macro_release",
        })
    return events


def _parse_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def fetch_yahoo_rss_news(ticker: str, limit: int = 10) -> List[Dict]:
    params = {"s": ticker, "region": "US", "lang": "en-US"}
    response = requests.get(YAHOO_RSS_URL, params=params, timeout=15)
    if response.status_code != 200:
        return []

    try:
        root = ET.fromstring(response.text)
    except ET.ParseError:
        return []

    events = []
    for item in root.findall(".//item")[:limit]:
        title = item.findtext("title")
        link = item.findtext("link")
        pub_date = item.findtext("pubDate")
        events.append({
            "timestamp": _parse_rss_date(pub_date),
            "title": title,
            "source": "Yahoo RSS",
            "url": link,
            "event_type": "company_rss",
        })
    return events


def _parse_rss_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        return None


def fetch_sec_filings(ticker: str, limit: int = 10) -> List[Dict]:
    cik_map = fetch_sec_ticker_map()
    cik = cik_map.get(ticker.upper())
    if cik is None:
        return []

    headers = {"User-Agent": get_sec_user_agent()}
    response = requests.get(SEC_SUBMISSIONS_URL.format(cik=cik), headers=headers, timeout=20)
    if response.status_code != 200:
        return []
    data = response.json()
    recent = data.get("filings", {}).get("recent", {})

    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    descriptions = recent.get("primaryDocDescription", [])

    events = []
    for idx in range(min(limit, len(forms))):
        events.append({
            "timestamp": _parse_date(dates[idx]),
            "title": f"{forms[idx]} filing",
            "source": "SEC EDGAR",
            "summary": descriptions[idx],
            "event_type": "sec_filing",
        })
    return events


_SEC_TICKER_CACHE: Optional[Dict[str, int]] = None


def fetch_sec_ticker_map() -> Dict[str, int]:
    global _SEC_TICKER_CACHE
    if _SEC_TICKER_CACHE is not None:
        return _SEC_TICKER_CACHE

    headers = {"User-Agent": get_sec_user_agent()}
    response = requests.get(SEC_TICKERS_URL, headers=headers, timeout=20)
    if response.status_code != 200:
        _SEC_TICKER_CACHE = {}
        return _SEC_TICKER_CACHE

    data = response.json()
    ticker_map = {}
    for item in data.values():
        ticker = item.get("ticker")
        cik = item.get("cik_str")
        if ticker and cik:
            ticker_map[ticker.upper()] = int(cik)

    _SEC_TICKER_CACHE = ticker_map
    return ticker_map
