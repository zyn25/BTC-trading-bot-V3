"""
Main backtest runner script.

Usage:
    python -m backtest.run_backtest --days 365 --balance 10000
    python -m backtest.run_backtest --days 180 --save-csv data/btc_6m.csv
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from backtest.data_loader import DataLoader
from backtest.strategy_tester import StrategyTester
from core.exchange import ExchangeManager
from config import settings
from utils.logger import logger


async def main():
    parser = argparse.ArgumentParser(description="BTC Trading Bot Backtester")
    parser.add_argument("--days", type=int, default=365, help="Days of historical data (default: 365)")
    parser.add_argument("--balance", type=float, default=10000, help="Initial balance (default: 10000)")
    parser.add_argument("--timeframe", type=str, default="15m", help="Timeframe (default: 15m)")
    parser.add_argument("--symbol", type=str, default=None, help="Symbol (default: from config)")
    parser.add_argument("--save-csv", type=str, default=None, help="Save data to CSV")
    parser.add_argument("--load-csv", type=str, default=None, help="Load data from CSV")
    parser.add_argument("--output", type=str, default="backtest_result.txt", help="Output report file")

    args = parser.parse_args()

    logger.info("🧪 BTC TRADING BOT - BACKTEST MODE")

    # Initialize exchange (untuk fetch data)
    exchange = ExchangeManager()
    await exchange.connect()

    try:
        # Load or fetch data
        loader = DataLoader(exchange)
        
        if args.load_csv:
            logger.info(f"📂 Loading from CSV: {args.load_csv}")
            df = loader.load_from_csv(args.load_csv)
        else:
            df = await loader.fetch_historical(
                symbol=args.symbol,
                timeframe=args.timeframe,
                days=args.days,
            )
            
            if args.save_csv:
                loader.save_to_csv(df, args.save_csv)

        # Run backtest
        tester = StrategyTester(initial_balance=args.balance)
        result = await tester.run(df, symbol=args.symbol or settings.trading.symbol)

        # Print report
        print("\n" + result["report"])

        # Save to file
        output_path = Path("backtests") / args.output
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["report"])
            f.write("\n\n=== TRADE DETAILS ===\n")
            for i, trade in enumerate(result["trades"], 1):
                f.write(
                    f"\n{i}. {trade['side'].upper()} @ {trade['entry_price']:.2f} → "
                    f"{trade.get('exit_price', 0):.2f} | "
                    f"PnL: {trade['pnl']:+.2f} ({trade['pnl_pct']:+.2f}%) | "
                    f"{trade['exit_reason']} | {trade['entry_time']} → {trade.get('exit_time')}\n"
                )

        logger.info(f"💾 Report saved to: {output_path}")

    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
