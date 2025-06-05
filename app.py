import streamlit as st
import requests

API_TOKEN = "c3ZWVXR5SmVnU3ZFbzRpRnE3M0NnYTctWUUtU19sblFyU3BwM3RMRlp3TT0"

st.title("Stock Mid Price Checker")

symbol = st.text_input("Enter stock ticker symbol:").upper()

if symbol:
    url = f"https://api.marketdata.app/v1/stocks/quotes/{symbol}/?extended=false&token={API_TOKEN}"

    response = requests.get(url)
    data = response.json()

    if "mid" in data and data["mid"]:
        price = data["mid"][0]
        st.write(f"Current mid price for {symbol}: ${price:.2f}")
    else:
        st.error("Mid price not found in API response.")
