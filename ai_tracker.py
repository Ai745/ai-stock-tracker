import yfinance as yf
import pandas as pd
import json
from datetime import datetime

# निफ्टी 50 और टॉप स्टॉक्स का ट्रैकिंग यूनिवर्स
STOCK_UNIVERSE = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "TATAMOTORS.NS",
    "ICICIBANK.NS", "ITC.NS", "LT.NS", "BHARTIARTL.NS", "MARUTI.NS",
    "SUNPHARMA.NS", "SBIN.NS", "HINDUNILVR.NS", "BAJFINANCE.NS", "ASIANPAINT.NS"
]

def analyze_stock(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    hist = stock.history(period="6mo")
    
    if hist.empty or "currentPrice" not in info:
        return None

    current_price = info.get("currentPrice", hist["Close"].iloc[-1])
    target_price = info.get("targetMeanPrice", current_price * 1.15)
    
    # 1. मोमेंटम और ट्रेंड एनालिसिस (50 EMA vs 200 EMA प्रॉक्सी)
    price_change_6m = ((hist["Close"].iloc[-1] - hist["Close"].iloc[0]) / hist["Close"].iloc[0]) * 100
    ma_50 = hist["Close"].rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else current_price

    # 2. फंडामेंटल स्कोरिंग (0 से 100)
    pe_ratio = info.get("trailingPE", 30)
    peg_ratio = info.get("pegRatio", 1.5)
    profit_margin = info.get("profitMargins", 0.1) * 100
    debt_to_equity = info.get("debtToEquity", 50)
    
    ai_score = 50 # बेस स्कोर
    
    # वैल्यूएशन और अर्निंग्स फैक्टर
    if peg_ratio and peg_ratio < 1.2: ai_score += 15
    elif peg_ratio and peg_ratio > 2.5: ai_score -= 10
    
    if profit_margin > 15: ai_score += 10
    if debt_to_equity < 80: ai_score += 10
    
    # मोमेंटम फैक्टर
    if current_price > ma_50: ai_score += 15
    if price_change_6m > 10: ai_score += 10

    ai_score = max(10, min(98, round(ai_score)))
    
    # 3. InvestingPro+ जैसा Fair Value & Upside
    upside_percent = round(((target_price - current_price) / current_price) * 100, 1)

    # 4. ऑटोमैटिक पोर्टफोलियो एक्शन (Add / Hold / Remove)
    if ai_score >= 75 and upside_percent > 10:
        action = "ADD TO PORTFOLIO"
        action_class = "buy"
    elif ai_score < 45 or upside_percent < -5:
        action = "REMOVE / EXIT"
        action_class = "sell"
    else:
        action = "HOLD"
        action_class = "hold"

    return {
        "ticker": ticker_symbol.replace(".NS", ""),
        "name": info.get("shortName", ticker_symbol),
        "price": round(current_price, 2),
        "fairValue": round(target_price, 2),
        "upside": upside_percent,
        "aiScore": ai_score,
        "action": action,
        "actionClass": action_class,
        "pe": round(pe_ratio, 1) if pe_ratio else "N/A",
        "trend": "Bullish" if current_price > ma_50 else "Consolidating"
    }

def run_screener():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Live AI Engine Running...")
    results = []
    
    for symbol in STOCK_UNIVERSE:
        try:
            data = analyze_stock(symbol)
            if data:
                results.append(data)
        except Exception as e:
            continue

    # AI स्कोर के आधार पर टॉप रिटर्न्स वाले स्टॉक्स को सॉर्ट करना
    results.sort(key=lambda x: x["aiScore"], reverse=True)
    
    # JSON फाइल में आउटपुट सेव करना
    with open("portfolio_data.json", "w") as f:
        json.dump({
            "lastUpdated": datetime.now().strftime("%d %b %Y, %I:%M %p"),
            "stocks": results
        }, f, indent=2)
        
    print("Done! Data saved to portfolio_data.json")

if __name__ == "__main__":
    run_screener()
