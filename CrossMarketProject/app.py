import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Cross Market Intelligence Dashboard",
    layout="wide",
    page_icon="📊"
)

# -------------------------------------------------
# DATABASE CONNECTION
# -------------------------------------------------
conn = sqlite3.connect("market_project.db", check_same_thread=False)

# -------------------------------------------------
# BANNER
# -------------------------------------------------
banner_path = os.path.join("assets", "banner.jpg")

if os.path.exists(banner_path):
    st.image(banner_path, use_container_width=True)
else:
    st.warning("Banner image not found inside assets folder")

st.title("🚀 Cross Market Intelligence Dashboard")

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
page = st.sidebar.radio(
    "Navigation",
    ["Home", "Market Snapshot", "SQL Analytics", "Crypto Analysis"]
)

# =================================================
# HOME
# =================================================
if page == "Home":

    st.header("Project Overview")

    st.write("""
    This dashboard integrates:
    - Cryptocurrency Data
    - Oil Market Data
    - Stock Market Data

    Built using:
    Python | SQL | Streamlit | Plotly
    """)

# =================================================
# MARKET SNAPSHOT
# =================================================
elif page == "Market Snapshot":

    st.header("📈 Cross Market Snapshot")

    # Get safe date range
    date_range = pd.read_sql(
        "SELECT MIN(date) as min_d, MAX(date) as max_d FROM crypto_prices;",
        conn
    )

    min_date = pd.to_datetime(date_range["min_d"][0])
    max_date = pd.to_datetime(date_range["max_d"][0])

    col1, col2 = st.columns(2)
    start = col1.date_input("Start Date", value=min_date)
    end = col2.date_input("End Date", value=max_date)

    query = f"""
    SELECT
        cp.date,
        cp.price_inr AS bitcoin,
        COALESCE(o.price_usd,0) AS oil,
        COALESCE(s1.close,0) AS sp500,
        COALESCE(s2.close,0) AS nifty
    FROM crypto_prices cp
    LEFT JOIN oil_prices o ON cp.date = o.date
    LEFT JOIN stock_prices s1 ON cp.date = s1.date AND s1.ticker='^GSPC'
    LEFT JOIN stock_prices s2 ON cp.date = s2.date AND s2.ticker='^NSEI'
    WHERE cp.coin_id='bitcoin'
    AND cp.date BETWEEN '{start}' AND '{end}'
    """

    df = pd.read_sql(query, conn)

    if not df.empty:

        # Convert properly
        df["date"] = pd.to_datetime(df["date"])
        df["bitcoin"] = pd.to_numeric(df["bitcoin"], errors="coerce").fillna(0)
        df["oil"] = pd.to_numeric(df["oil"], errors="coerce").fillna(0)
        df["sp500"] = pd.to_numeric(df["sp500"], errors="coerce").fillna(0)
        df["nifty"] = pd.to_numeric(df["nifty"], errors="coerce").fillna(0)

        # METRICS
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Bitcoin Avg", round(df["bitcoin"].mean(), 2))
        c2.metric("Oil Avg", round(df["oil"].mean(), 2))
        c3.metric("S&P 500 Avg", round(df["sp500"].mean(), 2))
        c4.metric("NIFTY Avg", round(df["nifty"].mean(), 2))

        # Convert to long format (avoids Plotly wide error)
        df_long = df.melt(
            id_vars=["date"],
            value_vars=["bitcoin", "oil", "sp500", "nifty"],
            var_name="Market",
            value_name="Price"
        )

        fig = px.line(
            df_long,
            x="date",
            y="Price",
            color="Market",
            template="plotly_dark",
            markers=True,
            title="Cross Market Comparison"
        )

        fig.update_layout(
            title_font_size=26,
            font=dict(size=14)
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df)

    else:
        st.warning("No data available for selected dates.")

# =================================================
# SQL ANALYTICS
# =================================================
elif page == "SQL Analytics":

    st.header("🧠 SQL Analytics Engine")

    queries = {
        "Total Crypto Records": "SELECT COUNT(*) FROM crypto_prices;",
        "Total Oil Records": "SELECT COUNT(*) FROM oil_prices;",
        "Total Stock Records": "SELECT COUNT(*) FROM stock_prices;",
        "Crypto Date Range": "SELECT MIN(date), MAX(date) FROM crypto_prices;",
        "Top 3 Cryptos by Market Cap":
            "SELECT name, market_cap FROM cryptocurrencies ORDER BY market_cap DESC LIMIT 3;",
        "Highest Bitcoin Price":
            "SELECT MAX(price_inr) FROM crypto_prices WHERE coin_id='bitcoin';",
        "Highest Oil Price":
            "SELECT MAX(price_usd) FROM oil_prices;",
        "Highest NASDAQ Close":
            "SELECT MAX(close) FROM stock_prices WHERE ticker='^IXIC';"
    }

    selected = st.selectbox("Select Query", list(queries.keys()))

    if st.button("Run Query"):
        result = pd.read_sql(queries[selected], conn)
        st.dataframe(result)

# =================================================
# CRYPTO ANALYSIS
# =================================================
elif page == "Crypto Analysis":

    st.header("🪙 Cryptocurrency Analysis")

    coins = pd.read_sql("SELECT DISTINCT coin_id FROM crypto_prices;", conn)
    coin = st.selectbox("Select Coin", coins["coin_id"])

    date_range = pd.read_sql(
        "SELECT MIN(date) as min_d, MAX(date) as max_d FROM crypto_prices;",
        conn
    )

    min_date = pd.to_datetime(date_range["min_d"][0])
    max_date = pd.to_datetime(date_range["max_d"][0])

    col1, col2 = st.columns(2)
    start = col1.date_input("Start Date", value=min_date, key="c1")
    end = col2.date_input("End Date", value=max_date, key="c2")

    query = f"""
    SELECT date, price_inr
    FROM crypto_prices
    WHERE coin_id='{coin}'
    AND date BETWEEN '{start}' AND '{end}'
    """

    df = pd.read_sql(query, conn)

    if not df.empty:

        df["price_inr"] = pd.to_numeric(df["price_inr"], errors="coerce").fillna(0)
        df["date"] = pd.to_datetime(df["date"])

        fig = px.line(
            df,
            x="date",
            y="price_inr",
            template="plotly_dark",
            markers=True,
            title=f"{coin.upper()} Price Trend"
        )

        fig.update_layout(title_font_size=26)

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df)

    else:
        st.warning("No data available.")
