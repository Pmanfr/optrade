import streamlit as st
import requests
import math
from scipy.stats import norm
from datetime import datetime, timedelta
import json
import os

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

    def to_dict(self):
        return {
            'optionSymbol': self.optionSymbol,
            'underlying': self.underlying,
            'strike': self.strike,
            'bid': self.bid,
            'side': self.side,
            'inTheMoney': self.inTheMoney,
            'dte': self.dte,
            'iv': self.iv,
            'ROI': self.ROI,
            'COP': self.COP,
            'x': self.x,
            'added_date': datetime.now().isoformat(),
            'expiration_date': (datetime.now() + timedelta(days=self.dte)).isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        trade = cls(
            data['optionSymbol'], data['underlying'], data['strike'], 
            data['bid'], data['side'], data['inTheMoney'], 
            data['dte'], data['iv'], data['ROI'], data['COP']
        )
        return trade

# User management functions
def load_users():
    if os.path.exists('users.json'):
        with open('users.json', 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)

def load_watchlist(username):
    if os.path.exists(f'watchlist_{username}.json'):
        with open(f'watchlist_{username}.json', 'r') as f:
            return json.load(f)
    return []

def save_watchlist(username, watchlist):
    with open(f'watchlist_{username}.json', 'w') as f:
        json.dump(watchlist, f, indent=2)

def get_current_price(symbol):
    try:
        current_price_url = f"https://api.marketdata.app/v1/stocks/quotes/{symbol}/?extended=false&token=emo4YXZySll1d0xmenMxTUVMb0FoN0xfT0Z1N00zRXZrSm1WbEoyVU9Sdz0"
        quote_data = requests.get(current_price_url).json()
        
        # Debug: Print the response to see structure
        print(f"API Response for {symbol}: {quote_data}")
        
        # Try different possible price fields
        if "mid" in quote_data and quote_data["mid"]:
            return quote_data["mid"][0]
        elif "last" in quote_data and quote_data["last"]:
            return quote_data["last"][0]
        elif "close" in quote_data and quote_data["close"]:
            return quote_data["close"][0]
        elif "ask" in quote_data and "bid" in quote_data:
            # Calculate mid price from bid/ask
            if quote_data["ask"] and quote_data["bid"]:
                ask = quote_data["ask"][0] if isinstance(quote_data["ask"], list) else quote_data["ask"]
                bid = quote_data["bid"][0] if isinstance(quote_data["bid"], list) else quote_data["bid"]
                return (ask + bid) / 2
        
        return None
    except Exception as e:
        print(f"Error getting price for {symbol}: {e}")
        return None

def get_earnings_date(symbol):
    """Get next earnings date for a symbol using API Ninjas"""
    try:
        # You'll need to get a free API key from https://www.api-ninjas.com/
        api_key = "YOUR_API_NINJAS_KEY"  # Replace with your actual API key
        headers = {
            'X-Api-Key': api_key
        }
        url = f"https://api.api-ninjas.com/v1/earningscalendar?ticker={symbol}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # Find the next upcoming earnings date
                for earning in data:
                    if earning.get('pricedate'):  # This is the earnings date
                        earnings_date = datetime.strptime(earning['pricedate'], '%Y-%m-%d')
                        if earnings_date >= datetime.now():
                            return earnings_date
        return None
    except Exception as e:
        print(f"Error fetching earnings for {symbol}: {e}")
        return None

def check_earnings_before_expiry(symbol, expiry_date):
    """Check if earnings occur before or on expiry date"""
    earnings_date = get_earnings_date(symbol)
    if earnings_date and earnings_date <= expiry_date:
        return True, earnings_date
    return False, None

def calculate_pnl(trade_data, current_price):
    strike = trade_data['strike']
    bid = trade_data['bid']
    
    # For put options
    if trade_data['side'] == 'put':
        # Premium collected
        premium_collected = bid * 100
        
        if current_price < strike:
            # Put is ITM - we lose money
            intrinsic_value = (strike - current_price) * 100
            pnl = premium_collected - intrinsic_value
            status = "Loss" if pnl < 0 else "Win"
        else:
            # Put is OTM - we keep the premium
            pnl = premium_collected
            status = "Win"
    
    return pnl, status

# Authentication
def login_page():
    st.title("🔐 Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to your account")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_btn"):
            users = load_users()
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    with tab2:
        st.subheader("Create new account")
        new_username = st.text_input("Choose Username", key="register_username")
        new_password = st.text_input("Choose Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        if st.button("Register", key="register_btn"):
            if new_password != confirm_password:
                st.error("Passwords don't match")
            elif len(new_username) < 3:
                st.error("Username must be at least 3 characters")
            elif len(new_password) < 4:
                st.error("Password must be at least 4 characters")
            else:
                users = load_users()
                if new_username in users:
                    st.error("Username already exists")
                else:
                    users[new_username] = new_password
                    save_users(users)
                    st.success("Account created successfully! Please login.")

# Main application
def main_app():
    st.title("🔍 Live Options Trade Scanner")
    
    # Logout button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
    
    with col1:
        st.write(f"Welcome, {st.session_state.username}!")
    
    # Navigation
    tab1, tab2, tab3 = st.tabs(["🔍 Scanner", "⭐ Watchlist", "📊 P&L Tracker"])
    
    with tab1:
        scanner_tab()
    
    with tab2:
        watchlist_tab()
    
    with tab3:
        pnl_tracker_tab()

def scanner_tab():
    st.header("Options Scanner")
    
    # ROI and COP range sliders
    roi_range = st.slider("📈 ROI Range", min_value=0.0, max_value=1.0, value=(0.20, 1.0), step=0.01)
    cop_range = st.slider("🎯 COP Range", min_value=0.0, max_value=1.0, value=(0.20, 1.0), step=0.01)

    # Use session_state to store trades
    if 'all_trades' not in st.session_state:
        st.session_state.all_trades = []

    if st.button("Generate Report"):
        st.session_state.all_trades.clear()
        companies = ["TSLA", "AMZN", "AMD", "PLTR", "RBLX", "LULU"]

        for company in companies:
            try:
                current_price_url = f"https://api.marketdata.app/v1/stocks/quotes/{company}/?extended=false&token=emo4YXZySll1d0xmenMxTUVMb0FoN0xfT0Z1N00zRXZrSm1WbEoyVU9Sdz0"
                quote_data = requests.get(current_price_url).json()
                current_price = quote_data["mid"][0]
                
                # Check for earnings before typical expiry (7 days from now)
                typical_expiry = datetime.now() + timedelta(days=7)
                has_earnings, earnings_date = check_earnings_before_expiry(company, typical_expiry)
                
                earnings_alert = ""
                if has_earnings:
                    earnings_str = earnings_date.strftime('%m/%d')
                    earnings_alert = f" ⚠️ **EARNINGS {earnings_str}**"
                
                st.session_state.all_trades.append(f"### 📈 {company} (Current Price: ${current_price:.2f}){earnings_alert}")

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

    # Display trades with add to watchlist option
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
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"<pre>{trade}</pre>", unsafe_allow_html=True)
                        with col2:
                            if st.button("⭐ Add", key=f"add_{trade.optionSymbol}"):
                                add_to_watchlist(trade)
                    trades_buffer = []

                st.markdown(item)  # Print the company header
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
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"<pre>{trade}</pre>", unsafe_allow_html=True)
                with col2:
                    if st.button("⭐ Add", key=f"add_{trade.optionSymbol}"):
                        add_to_watchlist(trade)

def add_to_watchlist(trade):
    watchlist = load_watchlist(st.session_state.username)
    trade_dict = trade.to_dict()
    
    # Check if trade already exists
    existing = any(item['optionSymbol'] == trade.optionSymbol for item in watchlist)
    if not existing:
        watchlist.append(trade_dict)
        save_watchlist(st.session_state.username, watchlist)
        st.success(f"Added {trade.optionSymbol} to watchlist!")
    else:
        st.warning("Trade already in watchlist!")

def watchlist_tab():
    st.header("Your Watchlist")
    
    watchlist = load_watchlist(st.session_state.username)
    
    if not watchlist:
        st.info("Your watchlist is empty. Add some trades from the scanner!")
        return
    
    # Group by underlying
    by_underlying = {}
    for trade in watchlist:
        underlying = trade['underlying']
        if underlying not in by_underlying:
            by_underlying[underlying] = []
        by_underlying[underlying].append(trade)
    
    for underlying, trades in by_underlying.items():
        # Check for earnings alert for this underlying
        current_price = get_current_price(underlying)
        if current_price:
            # Check if any trade has earnings before expiry
            has_earnings_alert = False
            earliest_earnings = None
            
            for trade in trades:
                expiry_date = datetime.fromisoformat(trade['expiration_date'])
                has_earnings, earnings_date = check_earnings_before_expiry(underlying, expiry_date)
                if has_earnings:
                    has_earnings_alert = True
                    if earliest_earnings is None or earnings_date < earliest_earnings:
                        earliest_earnings = earnings_date
            
            earnings_alert = ""
            if has_earnings_alert and earliest_earnings:
                earnings_str = earliest_earnings.strftime('%m/%d')
                earnings_alert = f" ⚠️ **EARNINGS {earnings_str}**"
            
            st.subheader(f"📈 {underlying} (${current_price:.2f}){earnings_alert}")
        else:
            st.subheader(f"📈 {underlying}")
        
        for i, trade in enumerate(trades):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                expiry_date = datetime.fromisoformat(trade['expiration_date']).strftime("%Y-%m-%d")
                st.write(f"**{trade['optionSymbol']}** | Strike: ${trade['strike']} | Bid: ${trade['bid']} | ROI: {trade['ROI']:.3f} | Expires: {expiry_date}")
            
            with col2:
                if st.button("🗑️ Remove", key=f"remove_{trade['optionSymbol']}_{i}"):
                    remove_from_watchlist(trade['optionSymbol'])

def remove_from_watchlist(option_symbol):
    watchlist = load_watchlist(st.session_state.username)
    watchlist = [trade for trade in watchlist if trade['optionSymbol'] != option_symbol]
    save_watchlist(st.session_state.username, watchlist)
    st.success(f"Removed {option_symbol} from watchlist!")
    st.rerun()

def pnl_tracker_tab():
    st.header("P&L Tracker")
    
    watchlist = load_watchlist(st.session_state.username)
    
    if not watchlist:
        st.info("No trades in watchlist to track!")
        return
    
    total_pnl = 0
    wins = 0
    losses = 0
    
    st.subheader("Expired/Current Positions")
    
    for trade in watchlist:
        expiry_date = datetime.fromisoformat(trade['expiration_date'])
        days_to_expiry = (expiry_date - datetime.now()).days
        
        current_price = get_current_price(trade['underlying'])
        
        if current_price is None:
            st.warning(f"Could not fetch current price for {trade['underlying']}")
            continue
        
        # Check for earnings before expiry
        has_earnings, earnings_date = check_earnings_before_expiry(trade['underlying'], expiry_date)
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            earnings_warning = ""
            if has_earnings and days_to_expiry > 0:  # Only show for active positions
                earnings_str = earnings_date.strftime('%m/%d')
                earnings_warning = f" ⚠️ Earnings {earnings_str}"
            
            st.write(f"**{trade['optionSymbol']}**{earnings_warning}")
            st.write(f"Strike: ${trade['strike']} | Current: ${current_price:.2f}")
        
        with col2:
            if days_to_expiry <= 0:
                st.write("🔴 **EXPIRED**")
                pnl, status = calculate_pnl(trade, current_price)
                total_pnl += pnl
                if status == "Win":
                    wins += 1
                else:
                    losses += 1
            else:
                st.write(f"⏰ {days_to_expiry} days")
                # For active positions, show unrealized P&L
                pnl, status = calculate_pnl(trade, current_price)
        
        with col3:
            color = "green" if pnl > 0 else "red"
            st.markdown(f"<span style='color: {color}'>${pnl:.2f}</span>", unsafe_allow_html=True)
        
        with col4:
            if days_to_expiry <= 0:
                emoji = "✅" if status == "Win" else "❌"
                st.write(f"{emoji} {status}")
            else:
                st.write("📊 Active")
    
    # Summary
    st.markdown("---")
    st.subheader("Summary (Expired Positions Only)")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total P&L", f"${total_pnl:.2f}")
    with col2:
        st.metric("Wins", wins)
    with col3:
        st.metric("Losses", losses)
    with col4:
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        st.metric("Win Rate", f"{win_rate:.1f}%")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

# Main app logic
if not st.session_state.logged_in:
    login_page()
else:
    main_app()
