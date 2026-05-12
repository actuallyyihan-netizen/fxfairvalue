from curses import window

import numpy as np
import pandas as pd

def zscore(s, window=756):
    mu = s.rolling(window, min_periods=max(60, window // 4)).mean()
    sd = s.rolling(window, min_periods=max(60, window // 4)).std()
    return (s - mu) / sd.replace(0, np.nan)

def align_to_daily(s, index):
    if s is None or len(s) == 0:
        return pd.Series(index=index, dtype=float)
    s = s.copy()
    s.index = pd.to_datetime(s.index)
    return s.reindex(index).ffill()

def yoy_inflation(cpi):
    return 100 * np.log(cpi / cpi.shift(12))

def ppp_fair_value(spot, cpi_base, cpi_quote, anchor_date=None):
    """Relative PPP: fair_t = spot_anchor * (CPI_quote/CPI_base)_t / same_anchor."""
    cpi_b = align_to_daily(cpi_base, spot.index)
    cpi_q = align_to_daily(cpi_quote, spot.index)
    rel = cpi_q / cpi_b
    valid = pd.concat([spot, rel], axis=1).dropna()
    if valid.empty:
        return pd.Series(index=spot.index, dtype=float, name="PPP_fair")

    anchor = valid.index[0] if anchor_date is None else pd.Timestamp(anchor_date)
    if anchor not in valid.index:
        anchor = valid.index[valid.index.get_indexer([anchor], method="nearest")[0]]
    fair = spot.loc[anchor] * rel / rel.loc[anchor]
    return fair.rename("PPP_fair")

def build_features(pair_spot, base, quote, macro, market, settings):
    idx = pair_spot.index
    window = int(settings.get("zscore_window_days", 756))
    cpi_b, cpi_q = macro.get(base, {}).get("cpi"), macro.get(quote, {}).get("cpi")
    rate_b, rate_q = macro.get(base, {}).get("rate"), macro.get(quote, {}).get("rate")

    ppp = ppp_fair_value(pair_spot, cpi_b, cpi_q)
    ppp_gap = np.log(ppp / pair_spot)

    infl_b = align_to_daily(yoy_inflation(cpi_b), idx)
    infl_q = align_to_daily(yoy_inflation(cpi_q), idx)

    real_5y = np.log(pair_spot / pair_spot.shift(1260)) - ((infl_q - infl_b) / 100.0)

    rate_diff = align_to_daily(rate_b, idx) - align_to_daily(rate_q, idx)
    infl_diff = infl_b - infl_q
    real_rate_diff = rate_diff - infl_diff
    growth_diff = pd.Series(0.0, index=idx)

    vix = align_to_daily(market.get("VIX"), idx) if market is not None and "VIX" in market else pd.Series(index=idx, dtype=float)
    risk_sentiment = -zscore(vix.pct_change(21), window)
    volatility = -zscore(vix, window)

    oil = align_to_daily(market.get("OIL"), idx) if market is not None and "OIL" in market else pd.Series(index=idx, dtype=float)
    gold = align_to_daily(market.get("GOLD"), idx) if market is not None and "GOLD" in market else pd.Series(index=idx, dtype=float)
    copper = align_to_daily(market.get("COPPER"), idx) if market is not None and "COPPER" in market else pd.Series(index=idx, dtype=float)

    oil_beta = oil.pct_change(21)
    copper_beta = copper.pct_change(21)
    gold_beta = gold.pct_change(21)

    # Placeholder REER gap:
    # In production, replace this with BIS REER deviation from rolling mean.
    # For now, this approximates broad real valuation using the PPP gap.
    reer_gap = ppp_gap.copy()

    # Placeholder terms of trade:
    # In production, replace with OECD terms-of-trade data.
    # For now, commodity-sensitive currencies are handled through split commodity betas.
    terms_of_trade = pd.concat([oil_beta, copper_beta, gold_beta], axis=1).mean(axis=1)

    # CNH policy proxy:
    # Uses CNH/CNY divergence, DXY pressure, and China equity risk proxy.
    # This is intentionally simple and easy to replace later with fixing-gap data.
    dxy = align_to_daily(market.get("DXY"), idx) if market is not None and "DXY" in market else pd.Series(index=idx, dtype=float)
    hsi = align_to_daily(market.get("HSI"), idx) if market is not None and "HSI" in market else pd.Series(index=idx, dtype=float)
    csi300 = align_to_daily(market.get("CSI300"), idx) if market is not None and "CSI300" in market else pd.Series(index=idx, dtype=float)

    china_equity_mom = pd.concat([hsi.pct_change(21), csi300.pct_change(21)], axis=1).mean(axis=1)
    cnh_policy_proxy = -dxy.pct_change(21) + china_equity_mom
    
    raw = pd.DataFrame({
        "ppp_gap": ppp_gap,
        "reer_momentum_5y": -real_5y,
        "rate_diff": rate_diff,
        "real_rate_diff": real_rate_diff,
        "inflation_diff": -infl_diff,
        "growth_diff": growth_diff,
        "risk_sentiment": risk_sentiment,
        "volatility": volatility,
        "oil_beta": oil_beta,
        "copper_beta": copper_beta,
        "gold_beta": gold_beta,
        "reer_gap": reer_gap,
        "terms_of_trade": terms_of_trade,
        "cnh_policy_proxy": cnh_policy_proxy,
    })

    z = raw.apply(lambda s: zscore(s, window))
    z["growth_diff"] = raw["growth_diff"]
    return raw, z, ppp

def fair_value_from_weights(spot, z_features, weights, scale=0.06):
    weights = pd.Series(weights, dtype=float)
    common = [c for c in z_features.columns if c in weights.index]
    composite = (z_features[common] * weights[common]).sum(axis=1, min_count=1)
    fv = spot * np.exp(scale * composite)
    misval = np.log(spot / fv)
    return pd.DataFrame({
        "spot": spot,
        "fair_value": fv,
        "composite_score": composite,
        "misvaluation_pct": 100 * (np.exp(misval) - 1),
    })

def forward_return_backtest(spot, misvaluation_pct, horizons=(5, 10, 20, 30), threshold_pct=2.0):
    rows = []
    for h in horizons:
        fwd = 100 * (spot.shift(-h) / spot - 1)
        sig = misvaluation_pct.abs() >= threshold_pct
        same = pd.DataFrame({"fwd_return_pct": fwd, "misvaluation_pct": misvaluation_pct})[sig].dropna()
        rows.append({
            "horizon_days": h,
            "n_signals": int(len(same)),
            "avg_forward_return_pct": same["fwd_return_pct"].mean() if len(same) else np.nan,
            "mean_reversion_hit_rate": (np.sign(same["fwd_return_pct"]) == -np.sign(same["misvaluation_pct"])).mean() if len(same) else np.nan,
        })
    return pd.DataFrame(rows)
