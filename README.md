# FX Fair Value Streamlit Monitor with Alpha Vantage CNH fallback

## Setup

```bash
cd ~/Downloads/fx_fair_value_streamlit_av
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Create `.env`:

```bash
touch .env
code .env
```

Inside `.env`:

```bash
ALPHAVANTAGE_API_KEY=your_actual_key_here
```

Then run:

```bash
streamlit cache clear
python -m streamlit run app.py
```

## Notes

- Yahoo/yfinance often fails for CNH.
- This version tries Yahoo first, then Alpha Vantage `FX_DAILY` for USD/CNH and USD/CNY.
- `.gitignore` is included to keep `.env` out of GitHub.
