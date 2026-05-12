import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yaml
from data_sources import get_usd_fx, build_pair_spot, get_macro_panel, get_market_panel, _get_av_key
from model import build_features, fair_value_from_weights, forward_return_backtest
from weight_presets import get_pair_preset_weights, DISPLAY_NAMES
from regression_validation import estimate_forward_return_betas, compare_preset_vs_regression

st.set_page_config(page_title="FX Fair Value Monitor", layout="wide")
st.title("FX Fair Value Monitor — G10 + CNY/CNH")
st.caption("A research dashboard for monitoring FX spot versus model-implied fair value across G10 and CNY/CNH pairs.")

@st.cache_data(ttl=3600)
def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

@st.cache_data(ttl=900)
def load_market(period, interval):
    return get_usd_fx(period, interval), get_market_panel(period, interval)

@st.cache_data(ttl=86400)
def load_macro(currencies):
    return get_macro_panel(currencies)

cfg = load_config()
settings = cfg["feature_settings"]
currencies = cfg["currencies"]

with st.sidebar:
    st.header("Pair")
    base = st.selectbox("Base currency", currencies, index=currencies.index("NZD") if "NZD" in currencies else 0)
    quote = st.selectbox("Quote currency", currencies, index=currencies.index("CNH") if "CNH" in currencies else 1)

    st.header("Data Status")
    if _get_av_key():
        st.success("Alpha Vantage key detected")
    else:
        st.warning("No Alpha Vantage key detected. CNH fallback may fail.")

    st.header("Model Settings")
    scale = st.slider(
        "Fair-Value Scale: 1; Composite Z-Score = x%",
        1.0, 15.0, float(settings["fair_value_scale"] * 100), 0.5
    ) / 100
    threshold = st.slider("Backtest Signal Threshold (%)", 0.5, 10.0, 2.0, 0.5)

    st.subheader("Indicator Weights")


    use_preset = st.checkbox("Use pair-specific sample weights", value=True)

    if use_preset:
        default_weights = get_pair_preset_weights(base, quote)
    else:
        default_weights = cfg["weights"]

    weights = {}

    weight_groups = {
        "Valuation": ["ppp_gap", "reer_momentum_5y", "reer_gap"],
        "Rates & Inflation": ["rate_diff", "real_rate_diff", "inflation_diff"],
        "Growth & Risk": ["growth_diff", "risk_sentiment", "volatility"],
        "Commodities": ["oil_beta", "copper_beta", "gold_beta", "terms_of_trade"],
    }

    if base in ["CNY", "CNH"] or quote in ["CNY", "CNH"]:
        weight_groups["China/CNH"] = ["cnh_policy_proxy"]

    for group_name, group_features in weight_groups.items():
        with st.expander(group_name, expanded=(group_name in ["Valuation", "Rates & Inflation"])):
            for k in group_features:
                if k in default_weights:
                    label = DISPLAY_NAMES.get(k, k)
                    weights[k] = st.number_input(
                        label,
                        value=float(default_weights[k]),
                        step=0.05,
                        format="%.3f",
                        key=f"weight_{base}_{quote}_{k}",
                    )
                    
    st.header("Regression Validation")

    run_regression = st.checkbox("Run regression validation", value=True)

    regression_horizon = st.selectbox(
        "Forward Return Horizon",
        options=[5, 10, 20, 30, 60],
        index=2,
    )

    regression_lookback = st.selectbox(
        "Regression Lookback Days",
        options=[500, 750, 1000, 1260, 1500],
        index=2,
    )

    prior_blend = st.slider(
        "Blend: Analyst's Prior Weight",
        min_value=0.0,
        max_value=1.0,
        value=0.70,
        step=0.05,
    )

try:
    usd_fx, market = load_market(settings["history_period"], settings["data_interval"])
    macro = load_macro(currencies)

    spot = build_pair_spot(base, quote, usd_fx)

    if len(spot.dropna()) < 260:
        st.warning(
            f"Only {len(spot.dropna())} usable data points for {base}/{quote}. "
            "The model needs at least ~260 daily observations for short-term z-scores, "
            "and ideally 5+ years for the 5Y real FX momentum feature."
        )

    raw, z, ppp = build_features(spot, base, quote, macro, market, settings)
    fv = fair_value_from_weights(spot, z, weights, scale)

    latest_df = fv.dropna()
    if latest_df.empty:
        raise ValueError("Fair value dataframe is empty after feature construction. Try shorter z-score window or another pair.")
    latest = latest_df.iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Spot", f"{latest['spot']:.4f}")
    c2.metric("Fair Value", f"{latest['fair_value']:.4f}")
    c3.metric("Spot vs Fair", f"{latest['misvaluation_pct']:.2f}%")
    c4.metric("Composite Score", f"{latest['composite_score']:.2f}")
    # Simple model confidence score
    latest_z = z.loc[fv.dropna().index[-1]]
    data_coverage = latest_z.notna().mean()

    signal_strength = min(abs(latest["composite_score"]) / 2.0, 1.0)

    usable_history = min(len(spot.dropna()) / 1260, 1.0)

    confidence_score = 100 * (
        0.45 * data_coverage
        + 0.30 * usable_history
        + 0.25 * signal_strength
    )

    confidence_label = (
        "High" if confidence_score >= 75
        else "Medium" if confidence_score >= 50
        else "Low"
    )

    st.info(
        f"Model confidence: **{confidence_label} ({confidence_score:.0f}/100)** | "
        f"Data coverage: {data_coverage:.0%} | "
        f"Usable history: {len(spot.dropna())} observations | "
        f"Signal strength: {signal_strength:.0%}"
    )

    st.subheader("Spot vs Fair Value Chart")

    chart_col1, chart_col2, chart_col3 = st.columns([1.2, 1.2, 1])

    with chart_col1:
        chart_window = st.selectbox(
            "Chart horizon",
            options=["1M", "3M", "6M", "YTD", "1Y", "3Y", "5Y", "All"],
            index=4,
        )

    with chart_col2:
        y_scale = st.selectbox(
            "Price scale",
            options=["Linear", "Log"],
            index=0,
        )

    with chart_col3:
        show_range_slider = st.checkbox("Show range slider", value=True)


    def filter_chart_window(df, window):
        df = df.dropna(how="all").copy()

        if df.empty or window == "All":
            return df

        end_date = df.index.max()

        if window == "1M":
            start_date = end_date - pd.DateOffset(months=1)
        elif window == "3M":
            start_date = end_date - pd.DateOffset(months=3)
        elif window == "6M":
            start_date = end_date - pd.DateOffset(months=6)
        elif window == "YTD":
            start_date = pd.Timestamp(year=end_date.year, month=1, day=1)
        elif window == "1Y":
            start_date = end_date - pd.DateOffset(years=1)
        elif window == "3Y":
            start_date = end_date - pd.DateOffset(years=3)
        elif window == "5Y":
            start_date = end_date - pd.DateOffset(years=5)
        else:
            start_date = df.index.min()

        return df.loc[df.index >= start_date]


    chart_df = pd.DataFrame({
        "Spot": fv["spot"],
        "Weighted Fair Value": fv["fair_value"],
    })

    if ppp.notna().sum() > 0:
        chart_df["Relative PPP Fair"] = ppp

    chart_df = filter_chart_window(chart_df, chart_window)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=chart_df.index,
        y=chart_df["Spot"],
        name="Spot",
        mode="lines",
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Spot: %{y:.4f}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=chart_df.index,
        y=chart_df["Weighted Fair Value"],
        name="Weighted Fair Value",
        mode="lines",
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Fair Value: %{y:.4f}<extra></extra>",
    ))

    if "Relative PPP Fair" in chart_df.columns:
        fig.add_trace(go.Scatter(
            x=chart_df.index,
            y=chart_df["Relative PPP Fair"],
            name="Relative PPP Fair",
            mode="lines",
            opacity=0.55,
            hovertemplate="Date: %{x|%Y-%m-%d}<br>PPP Fair: %{y:.4f}<extra></extra>",
        ))

    fig.update_layout(
        height=620,
        title=dict(
            text=f"{base}/{quote}: Spot vs Model Fair Value",
            font=dict(size=24),
        ),
        xaxis_title="Date",
        yaxis_title=f"{quote} per {base}",
        hovermode="x unified",
        dragmode="zoom",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="left",
            x=0,
        ),
        margin=dict(l=60, r=40, t=110, b=40),
    )

    fig.update_xaxes(
        rangeslider=dict(visible=show_range_slider),
    )

    fig.update_yaxes(
        type="log" if y_scale == "Log" else "linear",
        fixedrange=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displayModeBar": True,
            "modeBarButtonsToAdd": [
                "drawline",
                "drawopenpath",
                "eraseshape",
            ],
        },
    )

    st.subheader("Current Feature Contribution")
    contrib = z.mul(pd.Series(weights), axis=1).iloc[-1].sort_values()
    contrib_df = contrib.reset_index()
    contrib_df.columns = ["feature", "contribution"]
    contrib_df["feature"] = contrib_df["feature"].map(DISPLAY_NAMES).fillna(contrib_df["feature"])

    contrib_fig = go.Figure()
    contrib_fig.add_trace(go.Bar(
        x=contrib_df["contribution"],
        y=contrib_df["feature"],
        orientation="h",
        name="Contribution"
    ))
    contrib_fig.update_layout(height=430, xaxis_title="Weighted Z-Score Contribution", yaxis_title="")
    st.plotly_chart(contrib_fig, use_container_width=True)

    with st.expander("Debug: FX columns downloaded"):
        debug_fx = usd_fx.tail().copy()
        debug_fx.index = debug_fx.index.strftime("%Y-%m-%d")
        debug_fx = debug_fx.reset_index().rename(columns={"index": "Date"})
        debug_fx.index = debug_fx.index + 1
        st.write(debug_fx)
        st.write("Available columns:", list(usd_fx.columns))
        st.write("Rows per column:", usd_fx.count())

    st.subheader("Feature Z-Scores and Raw Inputs")


    # Take recent rows
    z_display = z.tail(10).copy()
    raw_display = raw.tail(10).copy()

    # Rename feature columns
    z_display = z_display.rename(columns=DISPLAY_NAMES)
    raw_display = raw_display.rename(columns=DISPLAY_NAMES)

    # Remove time component from date index
    z_display.index = z_display.index.strftime("%Y-%m-%d")
    raw_display.index = raw_display.index.strftime("%Y-%m-%d")

    # Combine with nicer top-level headers
    feature_table = pd.concat(
        {
            "Z-Score": z_display,
            "Raw": raw_display,
        },
        axis=1
    )

    feature_table = feature_table.reset_index()

    feature_table = feature_table.rename(columns={"index": "Date"})

    feature_table.index = feature_table.index + 1
    st.dataframe(feature_table, use_container_width=True)

    if run_regression:
        st.subheader("Regression Validation of Preset Weights")

        reg_table, reg_meta = estimate_forward_return_betas(
            spot=fv["spot"],
            z_features=z,
            horizon_days=regression_horizon,
            lookback_days=regression_lookback,
            min_obs=250,
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("Regression Observations", reg_meta["n_obs"])
        m2.metric("Regression R²", f"{reg_meta['r_squared']:.3f}" if pd.notna(reg_meta["r_squared"]) else "N/A")
        m3.metric("Adjusted R²", f"{reg_meta['adj_r_squared']:.3f}" if pd.notna(reg_meta["adj_r_squared"]) else "N/A")

        if reg_table.empty:
            st.warning(reg_meta["status"])
        else:
            reg_display = reg_table.copy()
            reg_display["feature"] = reg_display["feature"].map(DISPLAY_NAMES).fillna(reg_display["feature"])

            reg_display = reg_display.rename(columns={
                "feature": "Feature",
                "regression_beta": "Regression Beta",
                "regression_weight_normalized": "Regression Weight",
                "t_stat": "T-Statistic",
                "p_value": "p-Value",
            })
            reg_display.index = reg_display.index + 1
            st.dataframe(reg_display, use_container_width=True)

            comparison = compare_preset_vs_regression(
                preset_weights=weights,
                regression_table=reg_table,
                blend_prior_weight=prior_blend,
            )

            if not comparison.empty:
                comparison_display = comparison.copy()
                comparison_display["feature"] = comparison_display["feature"].map(DISPLAY_NAMES).fillna(comparison_display["feature"])

                comparison_display = comparison_display.rename(columns={
                    "feature": "Feature",
                    "preset_weight": "Preset Weight",
                    "regression_weight": "Regression Weight",
                    "sign_match": "Sign Match?",
                    "blended_weight": "Suggested Blended Weight",
                })

                st.subheader("Preset vs Regression Comparison")
                comparison_display.index = comparison_display.index + 1
                st.dataframe(comparison_display, use_container_width=True)

                sign_match_rate = comparison["sign_match"].dropna().mean()

                st.metric(
                    "Sign Match Rate",
                    f"{sign_match_rate:.0%}" if pd.notna(sign_match_rate) else "N/A"
                )
    st.subheader("Mean-Reversion Backtest")

    bt = forward_return_backtest(
        fv["spot"],
        fv["misvaluation_pct"],
        threshold_pct=threshold
    )

    bt = bt.rename(columns={
        "horizon_days": "Horizon Days",
        "n_signals": "No. of Signals",
        "avg_forward_return_pct": "Average Forward Return (%)",
        "mean_reversion_hit_rate": "Mean-Reversion Hit Rate",
    })
    bt.index = bt.index + 1
    st.dataframe(bt, use_container_width=True)

except Exception as e:
    st.error(f"Could not build model: {e}")
    st.info("For CNH: make sure .env exists, contains ALPHAVANTAGE_API_KEY=your_key, then run: streamlit cache clear")
