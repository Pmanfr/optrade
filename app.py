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

def load_user_watchlists(username):
    """Load all watchlists for a user"""
    if os.path.exists(f'watchlists_{username}.json'):
        with open(f'watchlists_{username}.json', 'r') as f:
            return json.load(f)
    return {}

def save_user_watchlists(username, watchlists):
    """Save all watchlists for a user"""
    with open(f'watchlists_{username}.json', 'w') as f:
        json.dump(watchlists, f, indent=2)

def create_watchlist(username, watchlist_name):
    """Create a new watchlist for a user"""
    watchlists = load_user_watchlists(username)
    if watchlist_name not in watchlists:
        watchlists[watchlist_name] = []
        save_user_watchlists(username, watchlists)
        return True
    return False

def delete_watchlist(username, watchlist_name):
    """Delete a watchlist for a user"""
    watchlists = load_user_watchlists(username)
    if watchlist_name in watchlists:
        del watchlists[watchlist_name]
        save_user_watchlists(username, watchlists)
        return True
    return False

def add_trade_to_watchlist(username, watchlist_name, trade_dict):
    """Add a trade to a specific watchlist"""
    watchlists = load_user_watchlists(username)
    if watchlist_name in watchlists:
        # Check if trade already exists
        existing = any(item['optionSymbol'] == trade_dict['optionSymbol'] for item in watchlists[watchlist_name])
        if not existing:
            watchlists[watchlist_name].append(trade_dict)
            save_user_watchlists(username, watchlists)
            return True
    return False

def remove_trade_from_watchlist(username, watchlist_name, option_symbol):
    """Remove a trade from a specific watchlist"""
    watchlists = load_user_watchlists(username)
    if watchlist_name in watchlists:
        watchlists[watchlist_name] = [trade for trade in watchlists[watchlist_name] if trade['optionSymbol'] != option_symbol]
        save_user_watchlists(username, watchlists)
        return True
    return False

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
        api_key = "eZQ1PiKHaSazbMk9zIcYOQ==L80sp50rXpuPuFWx"
        headers = {
            'X-Api-Key': api_key
        }
        # FIXED: Added show_upcoming=true to get future earnings dates
        url = f"https://api.api-ninjas.com/v1/earningscalendar?ticker={symbol}&show_upcoming=true"
        
        print(f"Requesting earnings for {symbol}: {url}")  # Debug print
        
        response = requests.get(url, headers=headers)
        
        print(f"Response status for {symbol}: {response.status_code}")  # Debug print
        print(f"Response content for {symbol}: {response.text}")  # Debug print
        
        if response.status_code == 200:
            data = response.json()
            print(f"Parsed data for {symbol}: {data}")  # Debug print
            
            if data and len(data) > 0:
                # Find the next upcoming earnings date
                current_date = datetime.now()
                upcoming_earnings = []
                
                for earning in data:
                    print(f"Processing earning record: {earning}")  # Debug print
                    
                    # FIXED: Use the correct field name 'date'
                    if 'date' in earning and earning['date']:
                        date_field = earning['date']
                        
                        try:
                            # FIXED: Handle the date format properly (YYYY-MM-DD)
                            earnings_date = datetime.strptime(date_field, '%Y-%m-%d')
                            
                            # Only consider future dates
                            if earnings_date.date() >= current_date.date():
                                upcoming_earnings.append(earnings_date)
                                print(f"Found upcoming earnings for {symbol}: {earnings_date}")
                        except ValueError as e:
                            print(f"Date parsing error for {symbol}: {e}")
                            continue
                
                if upcoming_earnings:
                    # Return the earliest upcoming earnings date
                    return min(upcoming_earnings)
                else:
                    print(f"No upcoming earnings found for {symbol}")
            else:
                print(f"No earnings data returned for {symbol}")
        else:
            print(f"API request failed for {symbol}: Status {response.status_code}, Response: {response.text}")
        
        return None
    except Exception as e:
        print(f"Error fetching earnings for {symbol}: {e}")
        return None

def get_major_economic_events():
    """Get major economic events using Finnhub API"""
    try:
        # Get a free API key from https://finnhub.io/register
        api_key = "d11u4k1r01qjtpe8vh30d11u4k1r01qjtpe8vh3g"  # Replace with your Finnhub API key
        
        # Get current date and next 7 days
        from datetime import datetime, timedelta
        today = datetime.now()
        end_date = today + timedelta(days=7)
        
        # Format dates for API (YYYY-MM-DD)
        start_date = today.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        url = f"https://finnhub.io/api/v1/calendar/economic?from={start_date}&to={end_date_str}&token={api_key}"
        
        print(f"Requesting economic events: {url}")  # Debug print
        
        response = requests.get(url)
        
        print(f"Economic events response status: {response.status_code}")  # Debug print
        
        if response.status_code == 200:
            data = response.json()
            economic_events = data.get('economicCalendar', [])
            
            # Filter for major US events that affect volatility
            major_events = []
            high_impact_keywords = [
                'fed', 'federal reserve', 'interest rate', 'fomc', 'powell',
                'inflation', 'cpi', 'ppi', 'pce', 'core inflation',
                'employment', 'unemployment', 'jobs', 'nonfarm', 'payroll',
                'gdp', 'gross domestic product',
                'retail sales', 'consumer spending',
                'trade', 'tariff', 'trade balance',
                'manufacturing', 'ism manufacturing',
                'housing', 'home sales', 'building permits',
                'consumer confidence', 'consumer sentiment', 'michigan',
                'existing home sales', 'new home sales'
            ]
            
            for event in economic_events:
                if isinstance(event, dict):
                    event_name = event.get('event', '').lower()
                    country = event.get('country', '')
                    impact = event.get('impact', '')
                    
                    # Focus on US events and high/medium impact events
                    if (country == 'US' and impact in ['high', 'medium']) or \
                       any(keyword in event_name for keyword in high_impact_keywords):
                        
                        # Parse the date (Finnhub format: YYYY-MM-DD HH:MM:SS)
                        try:
                            event_datetime = event.get('time', '')
                            if event_datetime:
                                # Convert timestamp to datetime
                                event_date = datetime.fromtimestamp(int(event_datetime))
                            else:
                                continue
                                
                            major_events.append({
                                'date': event_date,
                                'event': event.get('event', ''),
                                'country': event.get('country', ''),
                                'impact': event.get('impact', ''),
                                'actual': event.get('actual', ''),
                                'estimate': event.get('estimate', ''),
                                'prev': event.get('prev', '')
                            })
                        except (ValueError, TypeError):
                            continue
            
            # Sort by date
            major_events.sort(key=lambda x: x['date'])
            return major_events[:15]  # Return top 15 most relevant events
            
        else:
            print(f"Economic events API failed: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error fetching economic events: {e}")
        return []
        
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
#Homepage
def homescreen():
    """Beautiful homescreen for OpTrade"""
    # Custom CSS for the homescreen
    st.markdown("""
    <style>
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 4rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }
    
    .hero-title {
        font-size: 4rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        margin-bottom: 2rem;
        opacity: 0.9;
    }
    
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        text-align: center;
        margin: 1rem 0;
        transition: transform 0.3s ease;
        border-left: 4px solid #667eea;
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 1rem;
    }
    
    .feature-description {
        color: #666;
        line-height: 1.6;
    }
    
    .stats-container {
        background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 2rem 0;
    }
    
    .stat-item {
        margin: 1rem 0;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        display: block;
    }
    
    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    .cta-section {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
    }
    
    .cta-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 1rem;
    }
    
    .cta-description {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">📈 OpTrade</div>
        <div class="hero-subtitle">Advanced Options Trading Scanner & Analytics Platform</div>
        <p style="font-size: 1.1rem; opacity: 0.8; max-width: 600px; margin: 0 auto; margin-bottom: 2rem;">
            Discover profitable put-selling opportunities with real-time options scanning, 
            earnings alerts, and comprehensive P&L tracking. Built for smart traders.
        </p>
    </div>

    """, unsafe_allow_html=True)
    
    # Hero CTA Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 **Get Started - It's Free!**", 
                    key="hero_get_started_btn", 
                    help="Click to register or login",
                    type="primary"):
            st.session_state.show_auth = True
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
    # Feature Cards
    st.markdown("## ✨ **Powerful Features**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔍</div>
            <div class="feature-title">Smart Scanner</div>
            <div class="feature-description">
                Real-time options chain analysis with customizable ROI and 
                probability filters. Find the best put-selling opportunities instantly.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚠️</div>
            <div class="feature-title">Earnings Alerts</div>
            <div class="feature-description">
                Get warned about upcoming earnings that could impact your positions. 
                Never get caught off-guard by volatility events again.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">P&L Tracking</div>
            <div class="feature-description">
                Monitor your options performance with detailed profit/loss tracking, 
                win rates, and portfolio analytics across multiple watchlists.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Additional Features Row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⭐</div>
            <div class="feature-title">Watchlists</div>
            <div class="feature-description">
                Organize and track your favorite trades across multiple 
                customizable watchlists with real-time updates.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📅</div>
            <div class="feature-title">Economic Events</div>
            <div class="feature-description">
                Stay informed about major economic events that could 
                impact market volatility and your trading positions.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <div class="feature-title">Black-Scholes</div>
            <div class="feature-description">
                Advanced probability calculations using Black-Scholes model 
                to assess the likelihood of profitable outcomes.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Stats Section
    st.markdown("""
    <div class="stats-container">
        <h2 style="margin-bottom: 2rem;">📈 Platform Stats</h2>
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
            <div class="stat-item">
                <span class="stat-number">12+</span>
                <span class="stat-label">Major Stocks Tracked</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">Real-time</span>
                <span class="stat-label">Market Data</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">Advanced</span>
                <span class="stat-label">Analytics</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">Smart</span>
                <span class="stat-label">Filtering</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Call to Action
    st.markdown("""
    <div class="cta-section">
        <div class="cta-title">Ready to Start Trading Smarter?</div>
        <div class="cta-description">
            Join OpTrade today and discover profitable options opportunities with our advanced scanning tools.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem 0;">
        <p><strong>OpTrade</strong> - Advanced Options Trading Platform</p>
        <p>Built with ❤️ for smart traders | Real-time data • Smart analytics • Profitable insights</p>
    </div>
    """, unsafe_allow_html=True)

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
                    # Create a default watchlist for new users
                    create_watchlist(new_username, "Default")
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
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Scanner", "⭐ Watchlists", "📊 P&L Tracker", "📅 Economic Events"])
    
    with tab1:
        scanner_tab()
    
    with tab2:
        watchlists_tab()
    
    with tab3:
        pnl_tracker_tab()
        
    with tab4:
        economic_events_tab()


def scanner_tab():
    st.header("Options Scanner")
    
    # DTE and minimum bid sliders
    dte_value = st.slider("📅 Days to Expiration (DTE)", min_value=1, max_value=60, value=7, step=1)
    min_bid = st.slider("💰 Minimum Bid", min_value=0.01, max_value=5.0, value=0.10, step=0.01, format="%.2f")
    
    # ROI and COP range sliders
    roi_range = st.slider("📈 ROI Range", min_value=0.0, max_value=1.0, value=(0.20, 1.0), step=0.01)
    cop_range = st.slider("🎯 COP Range", min_value=0.0, max_value=1.0, value=(0.20, 1.0), step=0.01)

    # Use session_state to store trades
    if 'all_trades' not in st.session_state:
        st.session_state.all_trades = []

    if st.button("Generate Report"):
        st.session_state.all_trades.clear()
        companies = ["AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "BRK.B", "AVGO", "LLY", "JPM", "UNH", "XOM", "V", "PG", "JNJ", "MA", "HD", "NFLX", "ABBV", "CRM", "BAC", "ASML", "KO", "CVX", "AZN", "COST", "PEP", "TMO", "ORCL", "ACN", "LIN", "MRK", "ABT", "CSCO", "AMD", "DHR", "WMT", "VZ", "ADBE", "NOW", "TXN", "NEE", "COP", "QCOM", "AMGN", "PM", "SPGI", "RTX", "HON", "UNP", "T", "GS", "UBER", "LOW", "INTU", "CAT", "AMAT", "PFE", "SYK", "BKNG", "AXP", "VRTX", "DE", "TJX", "SCHW", "BSX", "AMT", "LMT", "PLD", "MDT", "BLK", "GILD", "ADP", "TMUS", "CI", "SLB", "CB", "REGN", "C", "FI", "MO", "SO", "EOG", "LRCX", "ZTS", "HCA", "PGR", "WM", "DUK", "ITW", "BMY", "APH", "MMC", "CSF", "NOC", "CME", "KLAC", "PNC", "ICE", "AON", "MSI", "CL", "EQIX", "SNPS", "FCX", "EMR", "TGT", "APD", "MCK", "FDX", "USB", "NSC", "COF", "SHW", "TFC", "ECL", "ROP", "MCO", "EL", "GM", "BDX", "GD", "PSX", "ADI", "HUM", "WELL", "CDNS", "PCAR", "DFS", "MPC", "JCI", "TRV", "GWW", "AJG", "CMG", "CTAS", "ORLY", "NXPI", "SRE", "AEP", "AFL", "AMP", "ALL", "AIG", "PAYX", "ROST", "CARR", "KMB", "D", "OXY", "NUE", "AME", "DXCM", "TEL", "A", "CCI", "FAST", "EXC", "CPRT", "O", "MRNA", "CTSH", "KR", "SPG", "CMI", "FTNT", "PWR", "EW", "MLM", "LULU", "LHX", "PCG", "PRU", "VRSK", "VST", "HLT", "EA", "IDXX", "F", "MNST", "EXR", "XEL", "ANET", "ADSK", "IQV", "WBA", "STZ", "DLR", "KHC", "DD", "PPG", "FANG", "GIS", "AWK", "ADM", "YUM", "WEC", "ED", "CSGP", "ON", "ANSS", "HPQ", "RMD", "BIIB", "DASH", "FTV", "GLW", "KEYS", "ETN", "IRM", "BK", "OTIS", "DOW", "WMB", "ROK", "AVB", "MTB", "PSA", "URI", "FRC", "ODFL", "EQR", "DHI", "VICI", "CTVA", "APTV", "VMC", "KMI", "RSG", "ILMN", "SBAC", "EBAY", "STT", "WY", "HPE", "LEN", "COO", "TROW", "DLTR", "ETR", "TSN", "ULTA", "MPWR", "CNC", "DVA", "NTRS", "DTE", "ARE", "VLO", "PHM", "ES", "WAB", "GPN", "ALGN", "CHD", "TSCO", "CBRE", "HAL", "RCL", "SIVB", "FE", "IR", "ENPH", "TT", "MAR", "DAL", "LVS", "BRO", "STE", "PPL", "AEE", "CMS", "HOLX", "STLD", "FITB", "HIG", "MKTX", "WTW", "TDG", "HBAN", "RF", "CAH", "EIX", "TYL", "CLX", "K", "IP", "CDW", "DGX", "WAT", "EXPD", "AVY", "ZBRA", "NTAP", "EXPE", "LYB", "FSLR", "CINF", "SWKS", "SYF", "PKI", "BALL", "CCL", "J", "NDAQ", "JBHT", "AMCR", "PFG", "LUV", "GRMN", "CFG", "POOL", "KEY", "INCY", "OMC", "VTRS", "FFIV", "UAL", "PEG", "WST", "AKAM", "TTWO", "LKQ", "L", "JKHY", "ZION", "NRG", "DOV", "PKG", "LDOS", "TPG", "TECH", "SJM", "EVRG", "IFF", "MHK", "WRB", "DRI", "HSY", "PAYC", "CE", "CTLT", "CBOE", "CZR", "GLW", "TER", "GDDY", "HSIC", "CTXS", "PTC", "CHRW", "STX", "MRVI", "VRSN", "TFX", "MOH", "JWN", "SEDG", "MAS", "CPT", "EQT", "LH", "BIO", "PEAK", "XYL", "NLOK", "ALLE", "DPZ", "BBWI", "FDS", "REG", "INVH", "PARA", "AOS", "GNRC", "UDR", "CNP", "LW", "JNPR", "TKO", "IEX", "TPR", "EMN", "MAA", "KIM", "ESS", "EXP", "CPB", "BWA", "NWSA", "WDC", "CRL", "HII", "RL", "SOLV", "COG", "SMCI", "AIZ", "NCLH", "EPAM", "PNR", "CAG", "APA", "GPC", "MTCH", "FMC", "BXP", "WYNN", "NWS", "ROL", "AAL", "NVR", "DVN", "BEN", "NI", "FOXA", "FOX", "LNT", "HAS", "MGM", "TAP", "UHS", "HRL", "WHR", "AAP", "PENN", "ALB", "IPG", "DISH", "QRVO", "NDSN", "NWL", "MOS", "HSBA", "MCHP", "FBIN", "NLSN", "SWK", "FRT", "RIVN"]        for company in companies:
            try:
                current_price_url = f"https://api.marketdata.app/v1/stocks/quotes/{company}/?extended=false&token=emo4YXZySll1d0xmenMxTUVMb0FoN0xfT0Z1N00zRXZrSm1WbEoyVU9Sdz0"
                quote_data = requests.get(current_price_url).json()
                current_price = quote_data["mid"][0]
                
                # Check for earnings before typical expiry (use dynamic DTE)
                typical_expiry = datetime.now() + timedelta(days=dte_value)
                has_earnings, earnings_date = check_earnings_before_expiry(company, typical_expiry)
                
                earnings_alert = ""
                if has_earnings:
                    earnings_str = earnings_date.strftime('%m/%d')
                    earnings_alert = f" ⚠️ **EARNINGS {earnings_str}**"
                
                st.session_state.all_trades.append(f"### 📈 {company} (Current Price: ${current_price:.2f}){earnings_alert}")

                options_chain_url = f"https://api.marketdata.app/v1/options/chain/{company}/?dte={dte_value}&minBid={min_bid:.2f}&side=put&range=otm&token=emo4YXZySll1d0xmenMxTUVMb0FoN0xfT0Z1N00zRXZrSm1WbEoyVU9Sdz0"
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
                                show_watchlist_selector(trade)
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
                        show_watchlist_selector(trade)

def show_watchlist_selector(trade):
    """Show modal to select watchlist for adding trade"""
    watchlists = load_user_watchlists(st.session_state.username)
    
    if not watchlists:
        st.error("No watchlists found. Please create a watchlist first.")
        return
    
    # Use session state to track the selected trade and show selector
    st.session_state.selected_trade = trade
    st.session_state.show_selector = True

@st.dialog("Select Watchlist")
def watchlist_selector_dialog():
    """Dialog for selecting watchlist"""
    if 'selected_trade' not in st.session_state:
        return
    
    trade = st.session_state.selected_trade
    watchlists = load_user_watchlists(st.session_state.username)
    
    st.write(f"**Adding:** {trade.optionSymbol}")
    st.write(f"**Strike:** ${trade.strike} | **ROI:** {trade.ROI:.3f}")
    
    selected_watchlist = st.selectbox(
        "Choose watchlist:",
        options=list(watchlists.keys()),
        key="watchlist_selector"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Add to Watchlist", key="confirm_add"):
            if add_trade_to_watchlist(st.session_state.username, selected_watchlist, trade.to_dict()):
                st.success(f"Added {trade.optionSymbol} to {selected_watchlist}!")
                st.session_state.selected_trade = None
                st.session_state.show_selector = False
                st.rerun()
            else:
                st.error("Trade already exists in this watchlist!")
    
    with col2:
        if st.button("Cancel", key="cancel_add"):
            st.session_state.selected_trade = None
            st.session_state.show_selector = False
            st.rerun()

def watchlists_tab():
    st.header("Your Watchlists")
    
    # Show watchlist selector dialog if needed
    if st.session_state.get('show_selector', False):
        watchlist_selector_dialog()
    
    watchlists = load_user_watchlists(st.session_state.username)
    
    # Watchlist management section
    st.subheader("📋 Manage Watchlists")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        new_watchlist_name = st.text_input("Create new watchlist:", key="new_watchlist_input")
    with col2:
        if st.button("➕ Create", key="create_watchlist_btn"):
            if new_watchlist_name.strip():
                if create_watchlist(st.session_state.username, new_watchlist_name.strip()):
                    st.success(f"Created watchlist: {new_watchlist_name}")
                    st.rerun()
                else:
                    st.error("Watchlist already exists!")
            else:
                st.error("Please enter a watchlist name")
    
    if not watchlists:
        st.info("No watchlists found. Create your first watchlist above!")
        return
    
    # Display watchlists
    for watchlist_name, trades in watchlists.items():
        with st.expander(f"📂 {watchlist_name} ({len(trades)} trades)", expanded=len(watchlists) == 1):
            # Delete watchlist button
            if len(watchlists) > 1:  # Don't allow deleting the last watchlist
                if st.button(f"🗑️ Delete {watchlist_name}", key=f"delete_watchlist_{watchlist_name}"):
                    if delete_watchlist(st.session_state.username, watchlist_name):
                        st.success(f"Deleted watchlist: {watchlist_name}")
                        st.rerun()
            
            if not trades:
                st.info("This watchlist is empty. Add some trades from the scanner!")
                continue
            
            # Group by underlying
            by_underlying = {}
            for trade in trades:
                underlying = trade['underlying']
                if underlying not in by_underlying:
                    by_underlying[underlying] = []
                by_underlying[underlying].append(trade)
            
            for underlying, underlying_trades in by_underlying.items():
                # Check for earnings alert for this underlying
                current_price = get_current_price(underlying)
                if current_price:
                    # Check if any trade has earnings before expiry
                    has_earnings_alert = False
                    earliest_earnings = None
                    
                    for trade in underlying_trades:
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
                    
                    st.write(f"**📈 {underlying} (${current_price:.2f})**{earnings_alert}")
                else:
                    st.write(f"**📈 {underlying}**")
                
                for i, trade in enumerate(underlying_trades):
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        expiry_date = datetime.fromisoformat(trade['expiration_date']).strftime("%Y-%m-%d")
                        st.write(f"**{trade['optionSymbol']}** | Strike: ${trade['strike']} | Bid: ${trade['bid']} | ROI: {trade['ROI']:.3f} | Expires: {expiry_date}")
                    
                    with col2:
                        if st.button("🗑️", key=f"remove_{watchlist_name}_{trade['optionSymbol']}_{i}"):
                            if remove_trade_from_watchlist(st.session_state.username, watchlist_name, trade['optionSymbol']):
                                st.success(f"Removed {trade['optionSymbol']} from {watchlist_name}!")
                                st.rerun()

def pnl_tracker_tab():
    st.header("📊 P&L Tracker")
    
    watchlists = load_user_watchlists(st.session_state.username)
    
    if not watchlists:
        st.info("No watchlists found to track!")
        return
    
    # Overall summary
    overall_pnl = 0
    overall_wins = 0
    overall_losses = 0
    
    # Process each watchlist
    for watchlist_name, trades in watchlists.items():
        if not trades:
            continue
            
        st.subheader(f"📂 {watchlist_name}")
        
        watchlist_pnl = 0
        watchlist_wins = 0
        watchlist_losses = 0
        
        for trade in trades:
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
                    watchlist_pnl += pnl
                    overall_pnl += pnl
                    if status == "Win":
                        watchlist_wins += 1
                        overall_wins += 1
                    else:
                        watchlist_losses += 1
                        overall_losses += 1
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
        
        # Watchlist summary
        if watchlist_wins > 0 or watchlist_losses > 0:
            st.markdown("**Watchlist Summary (Expired Only):**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                color = "green" if watchlist_pnl > 0 else "red"
                st.markdown(f"P&L: <span style='color: {color}'>${watchlist_pnl:.2f}</span>", unsafe_allow_html=True)
            with col2:
                st.write(f"Wins: {watchlist_wins}")
            with col3:
                st.write(f"Losses: {watchlist_losses}")
            with col4:
                win_rate = (watchlist_wins / (watchlist_wins + watchlist_losses) * 100) if (watchlist_wins + watchlist_losses) > 0 else 0
                st.write(f"Win Rate: {win_rate:.1f}%")
        
        st.markdown("---")
    
    # Overall summary
    if overall_wins > 0 or overall_losses > 0:
        st.subheader("🎯 Overall Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            color = "green" if overall_pnl > 0 else "red"
            st.markdown(f"<span style='color: {color}; font-weight: bold; font-size: 1.2em;'>Total P&L: ${overall_pnl:.2f}</span>", unsafe_allow_html=True)
        with col2:
            st.metric("Total Wins", overall_wins)
        with col3:
            st.metric("Total Losses", overall_losses)
        with col4:
            overall_win_rate = (overall_wins / (overall_wins + overall_losses) * 100) if (overall_wins + overall_losses) > 0 else 0
            st.metric("Win Rate", f"{overall_win_rate:.1f}%")


def economic_events_tab():
    """Tab for displaying major economic events"""
    st.header("📅 Major Economic Events This Week")
    st.write("*Events that could significantly impact options volatility*")
    
    # API key input section
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("🔑 **Get your FREE Finnhub API key:** https://finnhub.io/register")
        st.write("Replace 'YOUR_FINNHUB_API_KEY' in the code with your actual API key")
    
    if st.button("🔄 Refresh Events", key="refresh_economic_events"):
        # Clear any cached data
        if 'economic_events' in st.session_state:
            del st.session_state['economic_events']
    
    # Cache events in session state
    if 'economic_events' not in st.session_state:
        with st.spinner("Loading economic events..."):
            st.session_state.economic_events = get_major_economic_events()
    
    events = st.session_state.economic_events
    
    if not events:
        st.warning("⚠️ No major economic events found for this week.")
        st.info("This could mean:")
        st.write("- No major events scheduled")
        st.write("- API key not configured (check the code)")
        st.write("- API request failed")
        return
    
    st.success(f"Found {len(events)} major economic events this week")
    
    # Display events
    for event in events:
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 2])
            
            with col1:
                # Format date and time
                event_date = event['date']
                date_str = event_date.strftime('%a, %b %d')
                time_str = event_date.strftime('%I:%M %p')
                
                st.write(f"**📅 {date_str} at {time_str}**")
                st.write(f"🌍 {event['country']}")
            
            with col2:
                # Show volatility impact indicator based on Finnhub's impact rating
                impact = event.get('impact', '').lower()
                event_name_lower = event['event'].lower()
                
                if impact == 'high' or any(keyword in event_name_lower for keyword in ['fed', 'fomc', 'powell', 'interest rate']):
                    st.error("🔴 **HIGH IMPACT**")
                elif impact == 'medium' or any(keyword in event_name_lower for keyword in ['cpi', 'inflation', 'employment', 'jobs', 'gdp']):
                    st.warning("🟡 **MEDIUM IMPACT**")
                else:
                    st.info("🟢 **LOW-MED IMPACT**")
            
            with col3:
                st.write(f"**{event['event']}**")
                
                # Show estimate vs actual if available
                if event.get('estimate') and str(event['estimate']) != 'None':
                    st.write(f"📊 Estimate: {event['estimate']}")
                if event.get('prev') and str(event['prev']) != 'None':
                    st.write(f"📈 Previous: {event['prev']}")
                if event.get('actual') and str(event['actual']) != 'None':
                    st.write(f"✅ Actual: {event['actual']}")
            
            st.markdown("---")
    
    # Add educational note
    st.info("""
    **💡 Trading Tips for Put Sellers:**
    - **🔴 High Impact** events can cause 20-50%+ volatility spikes
    - **🟡 Medium Impact** events typically cause 5-20% volatility increases
    - **Avoid selling puts 1-2 days before major Fed announcements**
    - **CPI, Jobs, and GDP data** often move markets significantly
    - Consider **closing positions early** if major events approach
    - **Implied volatility** often rises before events and falls after (vol crush)
    """)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'show_auth' not in st.session_state:
    st.session_state.show_auth = False
# Main app logic

if not st.session_state.logged_in:
    if st.session_state.get('show_auth', False):
        login_page()
    else:
        homescreen()
else:
    main_app()
