import os
import time
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from dotenv import load_dotenv
from pandas_datareader import data as pdr

load_dotenv()

# Yahoo tickers. Most USD/XXX pairs are quoted as XXX=X on Yahoo.
YF_FX = {
    "EURUSD": ["EURUSD=X"],
    "GBPUSD": ["GBPUSD=X"],
    "AUDUSD": ["AUDUSD=X"],
    "NZDUSD": ["NZDUSD=X"],
    "USDJPY": ["JPY=X", "USDJPY=X"],
    "USDCHF": ["CHF=X", "USDCHF=X"],
    "USDCAD": ["CAD=X", "USDCAD=X"],
    "USDNOK": ["NOK=X", "USDNOK=X"],
    "USDSEK": ["SEK=X", "USDSEK=X"],
    "USDCNY": ["CNY=X", "USDCNY=X"],
    # yfinance often fails on CNH, so Alpha Vantage fallback is used below.
    "USDCNH": ["CNH=X", "USDCNH=X"],
}

FRED_CPI = {
    "USD": "CPIAUCSL", "EUR": "CP0000EZ19M086NEST", "JPY": "JPNCPIALLMINMEI",
    "GBP": "GBRCPIALLMINMEI", "CHF": "CHECPIALLMINMEI", "CAD": "CANCPIALLMINMEI",
    "AUD": "AUSCPIALLQINMEI", "NZD": "NZLCPIALLQINMEI", "NOK": "NORCPIALLMINMEI",
    "SEK": "SWECPIALLMINMEI", "CNY": "CHNCPIALLMINMEI", "CNH": "CHNCPIALLMINMEI",
}

FRED_POLICY = {
    "USD": "FEDFUNDS", "EUR": "ECBDFR", "JPY": "IRSTCI01JPM156N", "GBP": "IUDSOIA",
    "CHF": "IR3TIB01CHM156N", "CAD": "IRSTCI01CAM156N", "AUD": "IRSTCI01AUM156N",
    "NZD": "IRSTCI01NZM156N", "NOK": "IRSTCI01NOM156N", "SEK": "IRSTCI01SEM156N",
    "CNY": "IR3TIB01CNM156N", "CNH": "IR3TIB01CNM156N",
}

MARKET_TICKERS = {
    "VIX": ["^VIX"],
    "DXY": ["DX-Y.NYB"],
    "OIL": ["CL=F"],
    "GOLD": ["GC=F"],
    "COPPER": ["HG=F"],
    "HSI": ["^HSI"],
    "CSI300": ["000300.SS"],
}

def _get_av_key():
    key = os.getenv("ALPHAVANTAGE_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("ALPHAVANTAGE_API_KEY", None)
    except Exception:
        return None

def _download_one(ticker, period="10y", interval="1d"):
    try:
        raw = yf.download(ticker, period=period, interval=interval, auto_adjust=False, progress=False, threads=False)
        if raw is None or raw.empty:
            return pd.Series(dtype=float, name=ticker)
        if isinstance(raw.columns, pd.MultiIndex):
            s = raw["Close"].iloc[:, 0]
        else:
            s = raw["Close"]
        s.index = pd.to_datetime(s.index)
        return s.dropna().rename(ticker)
    except Exception:
        return pd.Series(dtype=float, name=ticker)

def _alpha_vantage_fx_daily(from_symbol, to_symbol, outputsize="full"):
    """
    Returns daily FX close series: to_symbol per 1 from_symbol.
    Example USD/CNH means CNH per 1 USD.
    Requires ALPHAVANTAGE_API_KEY in .env or Streamlit secrets.
    """
    key = _get_av_key()
    if not key:
        return pd.Series(dtype=float, name=f"{from_symbol}{to_symbol}")

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "FX_DAILY",
        "from_symbol": from_symbol,
        "to_symbol": to_symbol,
        "outputsize": outputsize,
        "apikey": key,
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        data = r.json()

        # Alpha Vantage sometimes sends Note/Error Message/Information.
        if "Time Series FX (Daily)" not in data:
            return pd.Series(dtype=float, name=f"{from_symbol}{to_symbol}")

        ts = data["Time Series FX (Daily)"]
        s = pd.Series({pd.Timestamp(k): float(v["4. close"]) for k, v in ts.items()})
        s = s.sort_index().rename(f"{from_symbol}{to_symbol}")
        return s
    except Exception:
        return pd.Series(dtype=float, name=f"{from_symbol}{to_symbol}")

def download_with_fallback(mapping, period="10y", interval="1d"):
    out = {}
    for name, tickers in mapping.items():
        found = pd.Series(dtype=float)
        for t in tickers:
            s = _download_one(t, period, interval)
            if len(s.dropna()) > 20:
                found = s.rename(name)
                break

        # Special CNH/CNY fallback via Alpha Vantage
        if len(found.dropna()) <= 20 and name in ("USDCNH", "USDCNY"):
            from_symbol, to_symbol = "USD", name[-3:]
            s = _alpha_vantage_fx_daily(from_symbol, to_symbol, outputsize="full")
            if len(s.dropna()) > 20:
                found = s.rename(name)

        out[name] = found.rename(name)

    df = pd.DataFrame(out).dropna(how="all").ffill()
    return df

def get_usd_fx(period="10y", interval="1d"):
    return download_with_fallback(YF_FX, period, interval)

def _get_usd_value_of_one_ccy(ccy, usd_fx):
    """
    Returns USD value of 1 unit of ccy.
    Example: EUR -> EURUSD; JPY -> 1/USDJPY; CNH -> 1/USDCNH.
    """
    ccy = ccy.upper()
    if ccy == "USD":
        return pd.Series(1.0, index=usd_fx.index, name="USD")

    direct = f"{ccy}USD"
    inverse = f"USD{ccy}"

    if direct in usd_fx.columns and usd_fx[direct].notna().sum() > 20:
        return usd_fx[direct].rename(ccy)

    if inverse in usd_fx.columns and usd_fx[inverse].notna().sum() > 20:
        return (1.0 / usd_fx[inverse]).rename(ccy)

    # Last resort: if CNH/CNY missing from combined panel, call Alpha Vantage directly.
    if ccy in ("CNH", "CNY"):
        s = _alpha_vantage_fx_daily("USD", ccy, outputsize="full")
        if len(s.dropna()) > 20:
            # Expand usd_fx-like index to the AV series index.
            return (1.0 / s).rename(ccy)

    raise KeyError(f"No usable FX data for {ccy}. Tried {direct}, {inverse}, Yahoo, and Alpha Vantage fallback.")

def build_pair_spot(base, quote, usd_fx):
    """Return BASE/QUOTE spot. Example: NZD/CNH = NZDUSD * USDCNH."""
    base, quote = base.upper(), quote.upper()
    if base == quote:
        raise ValueError("Base and quote cannot be the same.")

    base_usd = _get_usd_value_of_one_ccy(base, usd_fx)
    quote_usd = _get_usd_value_of_one_ccy(quote, usd_fx)

    idx = base_usd.index.union(quote_usd.index)
    base_usd = base_usd.reindex(idx).ffill()
    quote_usd = quote_usd.reindex(idx).ffill()

    spot = base_usd / quote_usd
    spot = spot.dropna().rename(f"{base}{quote}")
    return spot

def fred_series(series_id, start="1990-01-01"):
    try:
        s = pdr.DataReader(series_id, "fred", start)
        return s.iloc[:, 0].dropna()
    except Exception:
        return pd.Series(dtype=float, name=series_id)

def get_macro_panel(currencies, start="1990-01-01"):
    out = {}
    for c in currencies:
        cpi = fred_series(FRED_CPI.get(c, ""), start) if FRED_CPI.get(c) else pd.Series(dtype=float)
        rate = fred_series(FRED_POLICY.get(c, ""), start) if FRED_POLICY.get(c) else pd.Series(dtype=float)
        out[c] = {"cpi": cpi, "rate": rate}
    return out

def get_market_panel(period="10y", interval="1d"):
    return download_with_fallback(MARKET_TICKERS, period, interval)
