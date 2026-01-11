"""
Universe loader for SPY / QQQ / IWM / DIA constituents with caching.
"""

from pathlib import Path
from datetime import datetime, timedelta
import io
import pandas as pd
import requests

CACHE_DIR = Path(__file__).resolve().parent / "data"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL_DAYS = 7

def _cache_path(name):
    return CACHE_DIR / f"{name}.csv"

def _is_cache_valid(path):
    if not path.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age <= timedelta(days=CACHE_TTL_DAYS)

def _normalize_symbols(symbols):
    cleaned = []
    for symbol in symbols:
        if not isinstance(symbol, str):
            continue
        sym = symbol.strip().upper().replace(".", "-")
        if sym and sym.isascii():
            cleaned.append(sym)
    return sorted(set(cleaned))

def _write_cache(name, symbols):
    path = _cache_path(name)
    pd.DataFrame({"Symbol": symbols}).to_csv(path, index=False)

def _read_cache(name):
    path = _cache_path(name)
    if not _is_cache_valid(path):
        return None
    try:
        df = pd.read_csv(path)
        return _normalize_symbols(df["Symbol"].tolist())
    except Exception:
        return None

def _fetch_spy_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    for table in tables:
        if "Symbol" in table.columns:
            return _normalize_symbols(table["Symbol"].tolist())
    return []

def _fetch_qqq_symbols():
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    tables = pd.read_html(url)
    for table in tables:
        cols = [c.lower() for c in table.columns]
        if "ticker" in cols or "symbol" in cols:
            col_name = "Ticker" if "Ticker" in table.columns else "Symbol"
            return _normalize_symbols(table[col_name].tolist())
    return []

def _fetch_iwm_symbols():
    url = "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf/1467271812596.ajax?fileType=csv&fileName=IWM_holdings&dataType=fund"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    lines = response.text.splitlines()
    header_idx = None
    for idx, line in enumerate(lines):
        if line.startswith("Ticker"):
            header_idx = idx
            break
    if header_idx is None:
        return []
    csv_data = "\n".join(lines[header_idx:])
    df = pd.read_csv(io.StringIO(csv_data))
    if "Ticker" not in df.columns:
        return []
    return _normalize_symbols(df["Ticker"].tolist())

def _fetch_dia_symbols():
    url = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
    tables = pd.read_html(url)
    for table in tables:
        if "Symbol" in table.columns:
            return _normalize_symbols(table["Symbol"].tolist())
    return []

def get_universe_symbols(name):
    """Return symbols for SPY, QQQ, IWM, or DIA universe with caching."""
    name = name.upper()
    cached = _read_cache(name)
    if cached:
        return cached

    symbols = []
    try:
        if name == "SPY":
            symbols = _fetch_spy_symbols()
        elif name == "QQQ":
            symbols = _fetch_qqq_symbols()
        elif name == "IWM":
            symbols = _fetch_iwm_symbols()
        elif name == "DIA":
            symbols = _fetch_dia_symbols()
    except Exception:
        symbols = []

    if symbols:
        _write_cache(name, symbols)
    return symbols
