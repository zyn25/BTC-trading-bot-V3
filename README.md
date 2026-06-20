# 🤖 BTC Trading Bot v3.0 - Production Ready

Bot trading otomatis BTC/USDT dengan AI Hybrid (Technical + Groq LLM).

## ✨ Features
- 🤖 AI Hybrid: Technical Analysis + Groq LLM (FREE)
- 📊 Multi-strategy: Trend Following, Mean Reversion, Breakout
- 🛡️ Risk Management ketat (1% risk/trade, 3% daily max)
- 📱 Full Telegram Control (Commands + Inline Mode)
- 🔄 Multi-timeframe analysis
- ⚡ Auto trailing stop & partial TP
- 💾 SQLite/PostgreSQL persistence
- 🧪 Backtestable & tested

## 🚀 Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Setup env
cp .env.example .env
nano .env  # Add API keys

# 3. Run (testnet)
TESTNET=true python main.py

# 4. Production (LIVE)
TESTNET=false python main.py
