# weight_presets.py

"""
Source-informed sample weights.

These are analyst priors, not final estimated coefficients.
They are designed to be sensible defaults that users can override.
"""

FEATURES = [
    "ppp_gap",
    "reer_momentum_5y",
    "rate_diff",
    "real_rate_diff",
    "inflation_diff",
    "growth_diff",
    "risk_sentiment",
    "volatility",
    "oil_beta",
    "copper_beta",
    "gold_beta",
    "reer_gap",
    "terms_of_trade",
    "cnh_policy_proxy",
]

DISPLAY_NAMES = {
    "ppp_gap": "PPP Gap",
    "reer_momentum_5y": "5Y Real FX Value",
    "rate_diff": "Nominal Rate Differential",
    "real_rate_diff": "Real Rate Differential",
    "inflation_diff": "Inflation Differential",
    "growth_diff": "Growth Differential",
    "risk_sentiment": "Risk Sentiment",
    "volatility": "Market Volatility",
    "oil_beta": "Oil Beta",
    "copper_beta": "Copper Beta",
    "gold_beta": "Gold Beta",
    "reer_gap": "REER Gap",
    "terms_of_trade": "Terms of Trade",
    "cnh_policy_proxy": "CNH Policy Proxy",
}

REGIME_MULTIPLIERS = {
    "ppp_gap": 1.10,
    "reer_momentum_5y": 1.05,
    "rate_diff": 1.25,
    "real_rate_diff": 1.35,
    "inflation_diff": 1.20,
    "growth_diff": 0.85,
    "risk_sentiment": 1.20,
    "volatility": 1.15,
    "oil_beta": 1.35,
    "copper_beta": 1.25,
    "gold_beta": 1.10,
    "reer_gap": 1.10,
    "terms_of_trade": 1.20,
    "cnh_policy_proxy": 1.30,
}

CURRENCY_LOADINGS = {
    "USD": {
        "ppp_gap": 0.45,
        "reer_momentum_5y": 0.35,
        "rate_diff": 0.75,
        "real_rate_diff": 0.80,
        "inflation_diff": 0.45,
        "growth_diff": 0.50,
        "risk_sentiment": -0.30,
        "volatility": -0.35,
        "oil_beta": -0.20,
        "copper_beta": -0.10,
        "gold_beta": 0.20,
        "reer_gap": 0.60,
        "terms_of_trade": 0.10,
        "cnh_policy_proxy": 0.00,
    },
    "EUR": {
        "ppp_gap": 0.50,
        "reer_momentum_5y": 0.35,
        "rate_diff": 0.55,
        "real_rate_diff": 0.60,
        "inflation_diff": 0.35,
        "growth_diff": 0.45,
        "risk_sentiment": 0.10,
        "volatility": -0.05,
        "oil_beta": -0.25,
        "copper_beta": 0.00,
        "gold_beta": 0.00,
        "reer_gap": 0.60,
        "terms_of_trade": 0.20,
        "cnh_policy_proxy": 0.00,
    },
    "JPY": {
        "ppp_gap": 0.80,
        "reer_momentum_5y": 0.55,
        "rate_diff": 0.85,
        "real_rate_diff": 0.90,
        "inflation_diff": 0.35,
        "growth_diff": 0.25,
        "risk_sentiment": -0.85,
        "volatility": -0.80,
        "oil_beta": -0.45,
        "copper_beta": -0.10,
        "gold_beta": 0.30,
        "reer_gap": 0.75,
        "terms_of_trade": -0.20,
        "cnh_policy_proxy": 0.00,
    },
    "GBP": {
        "ppp_gap": 0.45,
        "reer_momentum_5y": 0.35,
        "rate_diff": 0.60,
        "real_rate_diff": 0.65,
        "inflation_diff": 0.45,
        "growth_diff": 0.45,
        "risk_sentiment": 0.20,
        "volatility": 0.05,
        "oil_beta": -0.10,
        "copper_beta": 0.00,
        "gold_beta": 0.00,
        "reer_gap": 0.55,
        "terms_of_trade": 0.10,
        "cnh_policy_proxy": 0.00,
    },
    "CHF": {
        "ppp_gap": 0.70,
        "reer_momentum_5y": 0.45,
        "rate_diff": 0.45,
        "real_rate_diff": 0.50,
        "inflation_diff": 0.25,
        "growth_diff": 0.20,
        "risk_sentiment": -0.75,
        "volatility": -0.75,
        "oil_beta": -0.30,
        "copper_beta": -0.10,
        "gold_beta": 0.40,
        "reer_gap": 0.70,
        "terms_of_trade": 0.10,
        "cnh_policy_proxy": 0.00,
    },
    "CAD": {
        "ppp_gap": 0.50,
        "reer_momentum_5y": 0.40,
        "rate_diff": 0.55,
        "real_rate_diff": 0.60,
        "inflation_diff": 0.35,
        "growth_diff": 0.40,
        "risk_sentiment": 0.35,
        "volatility": 0.10,
        "oil_beta": 0.95,
        "copper_beta": 0.20,
        "gold_beta": 0.05,
        "reer_gap": 0.60,
        "terms_of_trade": 0.75,
        "cnh_policy_proxy": 0.00,
    },
    "AUD": {
        "ppp_gap": 0.50,
        "reer_momentum_5y": 0.40,
        "rate_diff": 0.65,
        "real_rate_diff": 0.70,
        "inflation_diff": 0.45,
        "growth_diff": 0.50,
        "risk_sentiment": 0.85,
        "volatility": 0.35,
        "oil_beta": 0.10,
        "copper_beta": 0.95,
        "gold_beta": 0.15,
        "reer_gap": 0.60,
        "terms_of_trade": 0.85,
        "cnh_policy_proxy": 0.15,
    },
    "NZD": {
        "ppp_gap": 0.50,
        "reer_momentum_5y": 0.40,
        "rate_diff": 0.60,
        "real_rate_diff": 0.65,
        "inflation_diff": 0.40,
        "growth_diff": 0.45,
        "risk_sentiment": 0.80,
        "volatility": 0.30,
        "oil_beta": 0.05,
        "copper_beta": 0.55,
        "gold_beta": 0.10,
        "reer_gap": 0.60,
        "terms_of_trade": 0.65,
        "cnh_policy_proxy": 0.15,
    },
    "NOK": {
        "ppp_gap": 0.50,
        "reer_momentum_5y": 0.40,
        "rate_diff": 0.65,
        "real_rate_diff": 0.70,
        "inflation_diff": 0.45,
        "growth_diff": 0.40,
        "risk_sentiment": 0.45,
        "volatility": 0.20,
        "oil_beta": 1.10,
        "copper_beta": 0.15,
        "gold_beta": 0.05,
        "reer_gap": 0.60,
        "terms_of_trade": 0.90,
        "cnh_policy_proxy": 0.00,
    },
    "SEK": {
        "ppp_gap": 0.50,
        "reer_momentum_5y": 0.40,
        "rate_diff": 0.60,
        "real_rate_diff": 0.65,
        "inflation_diff": 0.40,
        "growth_diff": 0.50,
        "risk_sentiment": 0.50,
        "volatility": 0.20,
        "oil_beta": -0.10,
        "copper_beta": 0.15,
        "gold_beta": 0.00,
        "reer_gap": 0.60,
        "terms_of_trade": 0.20,
        "cnh_policy_proxy": 0.00,
    },
    "CNY": {
        "ppp_gap": 0.65,
        "reer_momentum_5y": 0.40,
        "rate_diff": 0.35,
        "real_rate_diff": 0.40,
        "inflation_diff": 0.25,
        "growth_diff": 0.75,
        "risk_sentiment": 0.20,
        "volatility": -0.10,
        "oil_beta": -0.20,
        "copper_beta": 0.45,
        "gold_beta": 0.05,
        "reer_gap": 0.70,
        "terms_of_trade": 0.50,
        "cnh_policy_proxy": 0.85,
    },
    "CNH": {
        "ppp_gap": 0.65,
        "reer_momentum_5y": 0.40,
        "rate_diff": 0.40,
        "real_rate_diff": 0.45,
        "inflation_diff": 0.25,
        "growth_diff": 0.75,
        "risk_sentiment": 0.30,
        "volatility": 0.00,
        "oil_beta": -0.20,
        "copper_beta": 0.50,
        "gold_beta": 0.05,
        "reer_gap": 0.70,
        "terms_of_trade": 0.50,
        "cnh_policy_proxy": 0.95,
    },
}


def get_pair_preset_weights(base: str, quote: str) -> dict:
    base = base.upper()
    quote = quote.upper()

    if base not in CURRENCY_LOADINGS:
        raise ValueError(f"No loading preset for base currency: {base}")

    if quote not in CURRENCY_LOADINGS:
        raise ValueError(f"No loading preset for quote currency: {quote}")

    weights = {}

    for feature in FEATURES:
        base_loading = CURRENCY_LOADINGS[base].get(feature, 0.0)
        quote_loading = CURRENCY_LOADINGS[quote].get(feature, 0.0)
        regime = REGIME_MULTIPLIERS.get(feature, 1.0)

        if feature in [
            "risk_sentiment",
            "volatility",
            "oil_beta",
            "copper_beta",
            "gold_beta",
            "terms_of_trade",
            "cnh_policy_proxy",
        ]:
            weight = (base_loading - quote_loading) * regime
        else:
            weight = ((base_loading + quote_loading) / 2) * regime

        weights[feature] = round(weight, 3)

    return weights