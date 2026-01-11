"""
Shared yfinance cache/throttle helpers for COREXIA.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import os
import time
from threading import Lock
from typing import Optional, Tuple

import streamlit as st
import yfinance as yf

YF_MIN_INTERVAL = float(os.getenv("COREXIA_YF_MIN_INTERVAL", "1.0"))
YF_MAX_RETRIES = int(os.getenv("COREXIA_YF_MAX_RETRIES", "4"))
YF_BACKOFF = float(os.getenv("COREXIA_YF_BACKOFF", "1.8"))

HIST_TTL = int(os.getenv("COREXIA_CACHE_TTL_HIST", "21600"))  # 6 hours
INTRA_TTL = int(os.getenv("COREXIA_CACHE_TTL_INTRA", "1800"))  # 30 min

_LAST_CALL = 0.0
_LOCK = Lock()


def _throttle():
    if YF_MIN_INTERVAL <= 0:
        return
    with _LOCK:
        now = time.monotonic()
        wait = YF_MIN_INTERVAL - (now - _LAST_CALL)
        if wait > 0:
            time.sleep(wait)
        globals()["_LAST_CALL"] = time.monotonic()


def _normalize_dates(start_date: datetime, end_date: datetime, interval: str) -> Tuple[datetime, datetime]:
    if interval in ("1d", "1wk"):
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        return start_date, end_date

    bucket_minutes = 30 if interval in ("30m", "90m") else 60
    end_date = end_date.replace(second=0, microsecond=0)
    end_date = end_date - timedelta(minutes=end_date.minute % bucket_minutes)
    start_date = start_date.replace(second=0, microsecond=0)
    return start_date, end_date


def _fetch_history(ticker: str, start_date: datetime, end_date: datetime, interval: str):
    delay = max(YF_MIN_INTERVAL, 0.1)
    for attempt in range(YF_MAX_RETRIES + 1):
        try:
            _throttle()
            return yf.Ticker(ticker).history(start=start_date, end=end_date, interval=interval)
        except Exception as exc:
            msg = str(exc).lower()
            if "too many requests" in msg or "rate" in msg:
                if attempt >= YF_MAX_RETRIES:
                    raise
                time.sleep(delay)
                delay *= YF_BACKOFF
                continue
            raise


@st.cache_data(ttl=HIST_TTL, show_spinner=False)
def _history_cached_slow(ticker: str, start_date: datetime, end_date: datetime, interval: str):
    return _fetch_history(ticker, start_date, end_date, interval)


@st.cache_data(ttl=INTRA_TTL, show_spinner=False)
def _history_cached_fast(ticker: str, start_date: datetime, end_date: datetime, interval: str):
    return _fetch_history(ticker, start_date, end_date, interval)


def history_cached(ticker: str, start_date: datetime, end_date: datetime, interval: str):
    start_date, end_date = _normalize_dates(start_date, end_date, interval)
    if interval in ("1d", "1wk"):
        return _history_cached_slow(ticker, start_date, end_date, interval)
    return _history_cached_fast(ticker, start_date, end_date, interval)


def _parse_period(period: str) -> Optional[timedelta]:
    if not period:
        return None
    unit = period[-1].lower()
    value_str = period[:-1]
    try:
        value = int(value_str)
    except ValueError:
        return None

    if unit == "d":
        return timedelta(days=value)
    if unit == "w":
        return timedelta(weeks=value)
    if unit == "m":
        return timedelta(days=value * 30)
    if unit == "y":
        return timedelta(days=value * 365)
    return None


def history_period_cached(ticker: str, period: str, interval: str = "1d"):
    delta = _parse_period(period)
    if delta is None:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
    else:
        end_date = datetime.now()
        start_date = end_date - delta
    return history_cached(ticker, start_date, end_date, interval)
