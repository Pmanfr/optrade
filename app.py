import streamlit as st
import requests
import math
from datetime import datetime, timedelta
from scipy.stats import norm

# Black-Scholes formula
def black_scholes_put(current_price, strike, bid, dte, iv):
    T = dte / 365.0
    d1 = (math.log(current_price / strike) + (0.5 * iv**2) * T) / (iv * math.sqrt(T))
    d2 = d1 - iv * math.sqrt(T)
    return norm.cdf(d2)

# Trade class
class Trade:
    def __init__(self, optionSymbol, underlying, strike, bid, side, inTheMoney, dte, iv, ROI, COP):
        self.optionSymbol = optionSymbol
        self.underlying = underlying
        self.strike = strike
        self.bid = bid
        self.side = side
        self.inTheMoney = inTheMoney
        self.dte = dte
        self.iv = iv
        self.ROI = ROI
        self.COP = COP
        self.x = ROI * COP

    def __str__(self):
        return (f"Option Symbol: {self.optionSymbol}, Underlying: {self.underlying}, "
                f"Strike: {self.strike}, Bid: {self.bid}, Side: {self.side}, "
                f"In The Money: {self.inTheMoney}, DTE: {self.dte}, IV: {self.iv}, "
                f"ROI: {self.ROI:.3f}, COP: {self.COP:.3f}, x: {self.x:.3f}")

# Streamlit app title
st.title("🔍 Live Options Trade Scanner")

# ROI and COP range sliders
roi_range = st.slider("📈 ROI Range", min_value=0.0, max_value=1.0, value=(0.20, 1.0), step=0.01)
cop_range = st.slider("🎯 COP Range", min_value=0.0, max_value=1.0, value=(0.20, 1.0), step=0.01)

# Session state initialization
if 'all_trades' not in st.session_state:
    st.session_state.all_trades = []
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []
if 'watchlist_dates' not in st.session_state:
    st.session_state.watchlist_dates = []

# Main trading logic
if st.button("Generate Report"):
    st.session_state.all_trades.clear()
    companies = ["TSLA", "AMZN", "AMD", "PLTR", "RBLX", "LULU"]

    for company in companies:
        try:
            current_price_url = f"https://api.marketdata.app/v1/stocks/quotes/{company}/?extended=false&token=emo4YXZySll1d0xmenMxTUVMb0FoN0xfT0Z1N00zRXZrSm1WbEoyVU9Sdz0"
            quote_data = requests.get(current_price_url).json()
            current_price = quote_data["mid"][0]
            st.session_state.all_trades.append(f"### 📈 {company} (Current Price: ${current_price:.2f})")

            options_chain_url = f"https://api.marketdata.app/v1/options/chain/{company}/?dte=7&minBid=0.20&side=put&range=otm&token=emo4YXZySll1d0xmenMxTUVMb0FoN0xfT0Z1N00zRXZrSm1WbEoyVU9Sdz0"
            chain_data = requests.get(options_chain_url).json()

            if chain_data.get("s") == "ok":
                for i in range(len(chain_data['strike'])):
                    strike = chain_data['strike'][i]
                    bid = chain_data['bid'][i]
                    ROI = round((bid * 100) / strike, 3)
                    dte = chain_data['dte'][i]
                    iv = chain_data['iv'][i]
                    COP = black_scholes_put(current_price, strike, bid, dte, iv)

                    if roi_range[0] <= ROI <= roi_range[1] and cop_range[0] <= COP <= cop_range[1]:
                        trade = Trade(
                            optionSymbol=chain_data['optionSymbol'][i],
                            underlying=chain_data['underlying'][i],
                            strike=strike,
                            bid=bid,
                            side=chain_data['side'][i],
                            inTheMoney=chain_data['inTheMoney'][i],
                            dte=dte,
                            iv=iv,
                            ROI=ROI,
                            COP=COP
                        )
                        st.session_state.all_trades.append(trade)
            else:
                st.session_state.all_trades.append(f"⚠️ No options data found for {company}")

        except Exception as e:
            st.session_state.all_trades.append(f"❌ Error processing {company}: {e}")

# Display and sort trades
if st.session_state.all_trades:
    st.markdown("---")
    sort_filter = st.selectbox("🔃 Sort trades by:", ["ROI", "COP", "x"], index=0)

    current_company = None
    trades_buffer = []

    for item in st.session_state.all_trades:
        if isinstance(item, str):
            if trades_buffer:
                if sort_filter == "ROI":
                    trades_buffer.sort(key=lambda t: t.ROI, reverse=True)
                elif sort_filter == "COP":
                    trades_buffer.sort(key=lambda t: t.COP, reverse=True)
                elif sort_filter == "x":
                    trades_buffer.sort(key=lambda t: t.x, reverse=True)

                for trade in trades_buffer:
                    st.markdown(f"<pre>{trade}</pre>", unsafe_allow_html=True)
                    if st.button(f"➕ Add to Watchlist ({trade.optionSymbol})"):
                        st.session_state.watchlist.append(trade)
                        st.session_state.watchlist_dates.append(datetime.now().date())
                trades_buffer = []
            st.markdown(item)
        else:
            trades_buffer.append(item)

    if trades_buffer:
        if sort_filter == "ROI":
            trades_buffer.sort(key=lambda t: t.ROI, reverse=True)
        elif sort_filter == "COP":
            trades_buffer.sort(key=lambda t: t.COP, reverse=True)
        elif sort_filter == "x":
            trades_buffer.sort(key=lambda t: t.x, reverse=True)

        for trade in trades_buffer:
            st.markdown(f"<pre>{trade}</pre>", unsafe_allow_html=True)
            if st.button(f"➕ Add to Watchlist ({trade.optionSymbol})"):
                st.session_state.watchlist.append(trade)
                st.session_state.watchlist_dates.append(datetime.now().date())

# Watchlist Section
st.markdown("---")
if st.button("📋 View Watchlist"):
    st.markdown("## 👀 Watchlist")
    updated_watchlist = []
    updated_dates = []

    for i, trade in enumerate(st.session_state.watchlist):
        added_date = st.session_state.watchlist_dates[i]
        days_passed = (datetime.now().date() - added_date).days
        remaining_dte = max(trade.dte - days_passed, 0)

        try:
            quote_url = f"https://api.marketdata.app/v1/stocks/quotes/{trade.underlying}/?extended=false&token=emo4YXZySll1d0xmenMxTUVMb0FoN0xfT0Z1N00zRXZrSm1WbEoyVU9Sdz0"
            current_price = requests.get(quote_url).json()["mid"][0]
        except:
            current_price = None

        result = "⏳ Still Active"
        color = "black"
        if remaining_dte == 0 and current_price is not None:
            if current_price > trade.strike:
                result = f"❌ Loss: ${int((current_price - trade.strike) * 100)}"
                color = "red"
            else:
                result = "✅ Win"
                color = "green"

        st.markdown(f"<pre>{trade}</pre>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:{color}; font-weight:bold'>{result}</span>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"DTE Left: {remaining_dte}")
        with col2:
            if st.button(f"❌ Remove ({trade.optionSymbol})"):
                continue  # Skip appending to updated lists, effectively removing it

        updated_watchlist.append(trade)
        updated_dates.append(added_date)

    st.session_state.watchlist = updated_watchlist
    st.session_state.watchlist_dates = updated_dates
