# regression_validation.py

import numpy as np
import pandas as pd
import statsmodels.api as sm


def _safe_normalize(series: pd.Series) -> pd.Series:
    """
    Normalize regression betas so the largest absolute beta is 1.
    Keeps signs.
    """
    s = series.replace([np.inf, -np.inf], np.nan).dropna()

    if s.empty:
        return series * np.nan

    max_abs = s.abs().max()

    if max_abs == 0 or pd.isna(max_abs):
        return series * np.nan

    return series / max_abs


def estimate_forward_return_betas(
    spot: pd.Series,
    z_features: pd.DataFrame,
    horizon_days: int = 20,
    lookback_days: int = 1000,
    min_obs: int = 250,
):
    """
    Estimate feature betas using forward FX returns.

    y_t = log(spot_{t+h} / spot_t) * 100

    A positive beta means:
    when the feature is high today, the base currency tends to appreciate
    against the quote currency over the selected horizon.
    """

    spot = spot.dropna().copy()
    spot.name = "spot"

    forward_return = np.log(spot.shift(-horizon_days) / spot) * 100
    forward_return.name = "forward_return_pct"

    df = pd.concat([forward_return, z_features], axis=1)
    df = df.replace([np.inf, -np.inf], np.nan).dropna()

    if lookback_days is not None and len(df) > lookback_days:
        df = df.tail(lookback_days)

    feature_cols = [c for c in z_features.columns if c in df.columns]

    valid_cols = []
    for c in feature_cols:
        if df[c].std(skipna=True) > 1e-8:
            valid_cols.append(c)

    feature_cols = valid_cols

    if len(df) < min_obs or len(feature_cols) == 0:
        empty = pd.DataFrame(
            columns=[
                "feature",
                "regression_beta",
                "regression_weight_normalized",
                "t_stat",
                "p_value",
            ]
        )

        meta = {
            "n_obs": len(df),
            "r_squared": np.nan,
            "adj_r_squared": np.nan,
            "horizon_days": horizon_days,
            "lookback_days": lookback_days,
            "status": "Not enough observations for regression.",
        }

        return empty, meta

    y = df["forward_return_pct"]
    X = df[feature_cols]
    X = sm.add_constant(X)

    model = sm.OLS(y, X).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": horizon_days},
    )

    params = model.params.drop("const", errors="ignore")
    tstats = model.tvalues.drop("const", errors="ignore")
    pvals = model.pvalues.drop("const", errors="ignore")

    normalized = _safe_normalize(params)

    result = pd.DataFrame(
        {
            "feature": params.index,
            "regression_beta": params.values,
            "regression_weight_normalized": normalized.reindex(params.index).values,
            "t_stat": tstats.reindex(params.index).values,
            "p_value": pvals.reindex(params.index).values,
        }
    )

    meta = {
        "n_obs": int(model.nobs),
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "horizon_days": horizon_days,
        "lookback_days": lookback_days,
        "status": "OK",
    }

    return result, meta


def compare_preset_vs_regression(
    preset_weights: dict,
    regression_table: pd.DataFrame,
    blend_prior_weight: float = 0.70,
) -> pd.DataFrame:
    """
    Compare source-informed preset weights against regression-implied weights.

    blended_weight
    = prior_weight * preset_weight
    + (1 - prior_weight) * regression_weight
    """

    if regression_table.empty:
        return pd.DataFrame()

    preset = pd.Series(preset_weights, name="preset_weight")

    reg = regression_table.set_index("feature")[
        "regression_weight_normalized"
    ]

    out = pd.concat([preset, reg], axis=1)

    out = out.rename(
        columns={
            "regression_weight_normalized": "regression_weight"
        }
    )

    out["sign_match"] = np.sign(out["preset_weight"]) == np.sign(out["regression_weight"])

    out.loc[
        (out["preset_weight"].abs() < 1e-8)
        | (out["regression_weight"].abs() < 1e-8),
        "sign_match",
    ] = np.nan

    out["blended_weight"] = (
        blend_prior_weight * out["preset_weight"]
        + (1 - blend_prior_weight) * out["regression_weight"]
    )

    out = out.reset_index().rename(columns={"index": "feature"})

    return out