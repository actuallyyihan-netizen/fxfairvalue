FX Fair Value Dashboard

A Streamlit-based FX fair value monitor for G10 currencies plus CNY/CNH.

The dashboard compares live FX spot against a model-implied fair value using valuation, interest rates, inflation, real rates, risk sentiment, volatility, commodities, terms-of-trade proxies, and CNH/CNY-specific indicators.

Live app: https://fxfairvalue.streamlit.app/

⸻

1. Project Overview

This project is a research dashboard designed to help monitor whether a currency pair is trading rich or cheap versus a model-implied fair value.

It supports the following currencies:

USD, EUR, JPY, GBP, CHF, CAD, AUD, NZD, NOK, SEK, CNY, CNH

The dashboard is built for macro/FX research use cases, especially for tracking:

* spot FX versus fair value
* valuation gaps
* macro driver contribution
* pair-specific factor sensitivities
* mean-reversion behavior
* regression validation of preset weights
* model confidence

This is not intended to be a black-box trading signal. It is a transparent monitoring tool where users can adjust assumptions and weights manually.

⸻

2. Core Model Logic

The model uses a weighted z-score framework.

Each indicator is converted into a z-score, then multiplied by a user-adjustable weight.

Composite Score = sum(weight_i × z_score_i)

Model fair value is then estimated as:

Fair Value = Spot × exp(scale × Composite Score)

Where:

* Spot is the latest exchange rate.
* Composite Score is the weighted macro/valuation signal.
* Scale controls how aggressively the fair value moves away from spot.
* Weights can be manually adjusted by the user.
* Pair-specific sample weights are provided as source-informed starting points.

A positive composite score pushes model fair value above spot.

A negative composite score pushes model fair value below spot.

⸻

3. Main Features

3.1 Spot vs Fair Value Chart

The main chart displays:

* live spot FX
* model-implied weighted fair value
* relative PPP fair value

The chart includes:

* selectable chart horizon
* linear/log price scale
* range slider
* zoom and pan tools
* hover values
* daily-level inspection

Supported chart horizons include:

1M, 3M, 6M, YTD, 1Y, 3Y, 5Y, All

⸻

3.2 Pair-Specific Sample Weights

The app includes pair-specific sample weights based on broad macro/FX intuition.

These weights are meant to be starting points, not final truth.

Examples:

* AUD and NZD receive higher risk-on and China/commodity sensitivity.
* CAD and NOK receive higher oil and terms-of-trade sensitivity.
* JPY and CHF receive safe-haven and volatility sensitivity.
* USD receives higher rates, real rates, and global liquidity sensitivity.
* CNH and CNY receive China growth, policy, and risk proxy sensitivity.

Users can override all weights manually from the sidebar.

The weight groups are organized into:

* Valuation
* Rates & Inflation
* Growth & Risk
* Commodities
* China/CNH

⸻

3.3 Feature Contribution

The dashboard shows the current contribution of each factor to the fair value model.

This helps answer:

Why is the model saying this currency pair is rich or cheap?

For example, for CAD/CNH, the model may show that oil, terms of trade, and China proxy variables are driving most of the signal.

For USD/JPY, rate differential and real-rate differential may dominate.

For AUD/JPY, risk sentiment and copper/commodity exposure may be more important.

⸻

3.4 Feature Z-Scores and Raw Inputs

The app displays both:

* z-scored indicators
* raw indicator values

This allows users to see whether a feature is historically stretched.

For example:

Oil Beta Z-Score = +1.5

means oil momentum is around 1.5 standard deviations above its rolling average.

⸻

3.5 Mean-Reversion Backtest

The app includes a simple mean-reversion backtest.

The user selects a misvaluation threshold, such as 2%.

The app then checks historical periods where:

absolute value of Spot vs Fair Value is greater than or equal to 2%

and measures what happened over forward horizons such as:

5 days, 10 days, 20 days, 30 days

The backtest table includes:

* number of historical signals
* average forward return
* mean-reversion hit rate

n_signals means the number of historical times the model found a large enough misvaluation to count as a signal.

⸻

3.6 Regression Validation

The dashboard can run a simple historical regression:

Forward FX Return ~ Feature Z-Scores

The purpose is to compare the preset weights with recent historical behavior.

The regression output includes:

* regression beta
* normalized regression weight
* t-stat
* p-value
* sign match
* suggested blended weight

Sign Match checks whether the preset weight and regression-implied weight point in the same direction.

Example:
Feature         Preset Weight  Regression Weight  Sign Match
Oil Beta        +0.80          +0.55              True
Risk Sentiment  +0.60          -0.25              False

A false sign match does not automatically mean the preset is wrong. It may reflect a short-term regime shift, noisy data, low R-squared, or an unusual market period.

⸻

3.7 Model Confidence Score

The dashboard includes a model confidence score.

It is based on:

* data coverage
* usable history length
* signal strength

The confidence score is designed to prevent over-interpreting weak or data-poor signals.

Example:

Model Confidence: Medium (68/100)

Data Coverage: 86%

Usable History: 1,250 observations

Signal Strength: 42%

A low confidence score means the model output should be treated carefully.

⸻

4. Indicators Used

4.1 PPP Gap

A long-run valuation anchor based on relative purchasing power.

This compares spot FX against an inflation-adjusted fair value estimate.

⸻

4.2 5-Year Real FX Value

A longer-term real exchange-rate value measure.

This is intended to capture whether a currency pair has become stretched over a multi-year horizon.

⸻

4.3 Nominal Rate Differential

The difference between base and quote interest-rate proxies.

This is useful because FX often responds to changes in front-end rates, carry, and monetary policy expectations.

⸻

4.4 Real Rate Differential

An inflation-adjusted version of rate differential.

Real Rate Differential = Nominal Rate Differential - Inflation Differential

This is especially useful for pairs such as:

USD/JPY, EUR/USD, GBP/USD, AUD/USD

⸻

4.5 Inflation Differential

The difference between base and quote inflation.

This affects purchasing power, real rates, and central-bank reaction functions.

⸻

4.6 Growth Differential

Currently implemented as a placeholder.

In future versions, this should be replaced with better growth proxies such as:

PMI, industrial production, OECD CLI, GDP nowcast, China activity indicators

⸻

4.7 Risk Sentiment

A market risk proxy based on VIX behavior.

Risk-on currencies such as AUD, NZD, SEK, and NOK tend to perform differently from safe-haven currencies such as JPY and CHF.

⸻

4.8 Market Volatility

A direct volatility feature based on VIX levels.

This is useful because FX fair value can shift during high-volatility periods, especially for safe havens and high-beta currencies.

⸻

4.9 Oil Beta

Oil momentum proxy.

Most relevant for:

CAD, NOK, JPY, EUR

CAD and NOK tend to have positive oil sensitivity.

JPY and EUR may be more negatively affected by higher energy-import costs.

⸻

4.10 Copper Beta

Copper momentum proxy.

Most relevant for:

AUD, NZD, CNH, CNY

Copper is used as a broad proxy for global manufacturing and China-linked demand.

⸻

4.11 Gold Beta

Gold momentum proxy.

Most relevant for:

CHF, JPY, USD, AUD

Gold can proxy for risk-off behavior, real-rate sensitivity, and safe-haven demand.

⸻

4.12 REER Gap

Currently implemented as a proxy based on PPP valuation.

In future versions, this should be replaced with direct BIS real effective exchange-rate data.

⸻

4.13 Terms of Trade

Currently implemented as a commodity basket proxy.

In future versions, this should be replaced with OECD or national terms-of-trade indices.

Terms of trade matter especially for commodity exporters such as:

AUD, CAD, NOK, NZD

⸻

4.14 CNH Policy Proxy

A simple CNH/CNY policy and China-risk proxy.

Currently uses:

DXY pressure, Hang Seng momentum, CSI 300 momentum

In future versions, this should be improved with:

CNH-CNY spread, USD/CNY fixing gap, China PMI, China credit impulse, onshore-offshore liquidity indicators

The CNH policy proxy is only economically relevant for pairs involving CNY or CNH.

⸻

5. Data Sources

The dashboard currently uses public data sources and market proxies.

5.1 Yahoo Finance via yfinance

Used for:

* G10 FX spot data
* market proxies
* VIX
* DXY
* oil
* copper
* gold
* equity index proxies

5.2 Alpha Vantage

Used as a fallback for:

USD/CNH and USD/CNY

This requires an API key.

5.3 FRED via pandas_datareader

Used for:

* CPI series
* interest-rate proxies
* policy-rate proxies where available

5.4 Proxy Data

Some indicators are currently proxies rather than direct institutional datasets.

Examples:

* REER gap is proxied using PPP gap.
* Terms of trade is proxied using commodity momentum.
* CNH policy proxy is proxied using DXY and China equity momentum.

These are acceptable for a research MVP, but should be upgraded for institutional use.

⸻

6. Local Installation

6.1 Clone the Repository

git clone https://github.com/actuallyyihan-netizen/fxfairvalue.git

cd fxfairvalue

6.2 Create a Virtual Environment

Use Python 3.11.

#python3.11 -m venv .venv

source .venv/bin/activate

6.3 Install Dependencies

#pip install –upgrade pip setuptools wheel

#pip install -r requirements.txt

6.4 Add Alpha Vantage API Key

Create a local .env file:

#touch .env

Inside .env, add:

ALPHAVANTAGE_API_KEY=your_actual_api_key_here

Do not upload .env to GitHub.

6.5 Run the App

#python -m streamlit run app.py

The app should open locally at:

http://localhost:8501

⸻

7. Streamlit Cloud Deployment

This app can be deployed on Streamlit Community Cloud.

Recommended settings:

Repository: actuallyyihan-netizen/fxfairvalue

Branch: main

Main file path: app.py

Python version: 3.11

In Streamlit Cloud secrets, add:

ALPHAVANTAGE_API_KEY = “your_actual_api_key_here”

Do not upload .env to GitHub.

⸻

8. Requirements

The app requires the following Python packages:

* streamlit
* pandas
* numpy
* plotly
* yfinance
* pandas-datareader
* pyyaml
* python-dotenv
* requests
* statsmodels

See requirements.txt for the exact package list and pinned versions.

⸻

9. GitHub Safety Notes

The repository should not include:

* .env
* .venv/
* pycache/
* .pyc files
* .streamlit/secrets.toml
* .DS_Store

These are excluded using .gitignore.

If an API key is accidentally uploaded, regenerate the API key immediately.

⸻

10. Current Limitations

This is a research MVP, so there are important limitations.

10.1 Some Features Are Proxies

REER gap, terms of trade, and CNH policy variables are currently approximations.

They should be improved with direct datasets in future versions.

10.2 Public Data Can Be Noisy

Yahoo Finance and free APIs can have missing values, delays, or inconsistent ticker coverage.

CNH data is especially inconsistent on Yahoo, which is why Alpha Vantage fallback is included.

10.3 Weights Are Analyst Priors

The default weights are source-informed sample weights.

They are not final statistically estimated coefficients.

Users should treat them as starting points and adjust them based on their own view.

10.4 Regression Is Not a Forecasting Guarantee

Regression validation helps compare preset weights with recent historical data, but it does not guarantee future performance.

FX regimes change frequently.

10.5 Fair Value Is Not a Trading Signal

A currency can stay rich or cheap for a long time.

Fair value gaps should be combined with:

* macro catalysts
* positioning
* central-bank events
* technical levels
* volatility
* risk management

⸻

11. Suggested Workflow

A typical user workflow:

1. Select a currency pair.
2. Check spot versus model fair value.
3. Review the model confidence score.
4. Check which factors are driving the signal.
5. Inspect z-scores and raw inputs.
6. Review mean-reversion backtest.
7. Run regression validation if needed.
8. Adjust weights manually based on current market view.
9. Use the output as a research input, not a standalone trade signal.

⸻

12. Example Use Cases

12.1 NZD/CNH

Useful for monitoring:

* China-linked growth sensitivity
* risk sentiment
* commodity proxies
* CNH policy pressure
* NZD carry and inflation dynamics

12.2 AUD/JPY

Useful for monitoring:

* global risk appetite
* commodities
* carry
* real-rate differentials
* JPY safe-haven dynamics

12.3 USD/JPY

Useful for monitoring:

* nominal rate differential
* real rate differential
* PPP valuation
* JPY undervaluation
* volatility and intervention risk

12.4 CAD/CNH

Useful for monitoring:

* oil sensitivity
* terms-of-trade proxy
* China growth proxy
* CNH policy pressure
* CAD real-rate dynamics

12.5 EUR/CHF

Useful for monitoring:

* safe-haven demand
* European growth/rates
* inflation differential
* valuation gap
* volatility sensitivity

⸻

13. Future Improvements

Planned improvements include:

13.1 Better REER Data

Replace the current REER proxy with direct BIS real effective exchange-rate data.

13.2 Better Terms-of-Trade Data

Replace the commodity proxy with direct OECD or national terms-of-trade indices.

13.3 Better Rate Data

Add:

* 2-year yield differentials
* real 2-year yield differentials
* yield curve slope differentials
* OIS-implied policy rates

13.4 Better China/CNH Variables

Add:

* CNH-CNY spread
* USD/CNY fixing gap
* China PMI
* China credit impulse proxy
* China trade data
* onshore/offshore liquidity proxy

13.5 Better Commodity Proxies

Add:

* iron ore
* LNG
* agricultural commodities
* broad commodity indices
* country-specific export baskets

13.6 Better Regime Detection

Add automatic regime classification, such as:

* risk-on
* risk-off
* USD liquidity stress
* commodity shock
* China growth shock
* central-bank repricing

13.7 Better Model Blending

Blend:

* source-informed prior weights
* rolling regression weights
* regime-adjusted weights

13.8 Exportable Reports

Add the ability to download:

* PDF reports
* CSV signal history
* PNG charts
* pair summary sheets

⸻

14. References
Current implemented data sources:

* Yahoo Finance via yfinance
* Alpha Vantage
* FRED via pandas_datareader

Currently proxied but intended future institutional sources:

* BIS REER data
* OECD terms-of-trade data

Research references:

* Currency Value paper
* GSDEER paper
* FX Short-Term Fair Value Modelling deck

⸻

15. Disclaimer

This dashboard is for research and educational purposes only.

It is not investment advice, financial advice, or a recommendation to buy or sell any currency.

Users should perform their own analysis and risk management before making any financial decisions.