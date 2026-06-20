"""
Generate formatted backtest report.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List


def generate_report(metrics: Dict, trades: List[Dict], 
                     initial_balance: float, final_balance: float,
                     equity_curve: List[float]) -> str:
    """Generate beautiful backtest report."""
    
    if not metrics:
        return "❌ No metrics to display"

    sign_pnl = "+" if metrics["total_pnl"] >= 0 else ""
    sign_return = "+" if metrics["total_return_pct"] >= 0 else ""
    pf_emoji = "✅" if metrics["profit_factor"] >= 1.5 else "⚠️" if metrics["profit_factor"] >= 1.0 else "❌"
    wr_emoji = "✅" if metrics["winrate"] >= 55 else "⚠️" if metrics["winrate"] >= 45 else "❌"
    dd_emoji = "✅" if metrics["max_drawdown_pct"] <= 15 else "⚠️" if metrics["max_drawdown_pct"] <= 25 else "❌"
    sharpe_emoji = "✅" if metrics["sharpe_ratio"] >= 1.5 else "⚠️" if metrics["sharpe_ratio"] >= 1.0 else "❌"

    # Grade
    score = 0
    if metrics["profit_factor"] >= 1.5: score += 2
    elif metrics["profit_factor"] >= 1.0: score += 1
    if metrics["winrate"] >= 55: score += 2
    elif metrics["winrate"] >= 45: score += 1
    if metrics["max_drawdown_pct"] <= 15: score += 2
    elif metrics["max_drawdown_pct"] <= 25: score += 1
    if metrics["sharpe_ratio"] >= 1.5: score += 2
    elif metrics["sharpe_ratio"] >= 1.0: score += 1
    if metrics["total_return_pct"] >= 20: score += 2
    elif metrics["total_return_pct"] >= 0: score += 1

    grade = "A+" if score >= 9 else "A" if score >= 8 else "B+" if score >= 7 else "B" if score >= 6 else "C" if score >= 4 else "D"

    report = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🧪 <b>BACKTEST REPORT</b>
  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>PERFORMANCE</b>
━━━━━━━━━━━━━━━━━━━━
Initial: <code>${initial_balance:,.2f}</code>
Final: <code>${final_balance:,.2f}</code>
Total PnL: <code>{sign_pnl}{metrics['total_pnl']:,.2f} USDT</code>
Return: <code>{sign_return}{metrics['total_return_pct']:.2f}%</code>
Grade: <b>{grade}</b> (Score: {score}/10)

📊 <b>TRADES</b>
━━━━━━━━━━━━━━━━━━━━
Total: <b>{metrics['total_trades']}</b>
Winners: <b>{metrics['win_count']}</b> ✅
Losers: <b>{metrics['loss_count']}</b> ❌
Win Rate: {wr_emoji} <b>{metrics['winrate']:.1f}%</b>

💵 <b>PROFIT METRICS</b>
━━━━━━━━━━━━━━━━━━━━
Avg Win: <code>+{metrics['avg_win']:.2f} USDT</code>
Avg Loss: <code>{metrics['avg_loss']:.2f} USDT</code>
Avg R:R: <b>1:{metrics['avg_rr']:.2f}</b>
Profit Factor: {pf_emoji} <b>{metrics['profit_factor']:.2f}</b>
Expectancy: <code>{metrics['expectancy']:.2f} USDT/trade</code>

📉 <b>RISK METRICS</b>
━━━━━━━━━━━━━━━━━━━━
Max Drawdown: {dd_emoji} <code>{metrics['max_drawdown_pct']:.2f}%</code>
Sharpe Ratio: {sharpe_emoji} <b>{metrics['sharpe_ratio']:.2f}</b>
Max Consecutive Wins: <b>{metrics['max_consecutive_wins']}</b>
Max Consecutive Losses: <b>{metrics['max_consecutive_losses']}</b>

🏆 <b>EXTREMES</b>
━━━━━━━━━━━━━━━━━━━━
Best Trade: <code>+{metrics['best_trade']:.2f} USDT</code>
Worst Trade: <code>{metrics['worst_trade']:.2f} USDT</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    # Recommendation
    if grade in ["A+", "A"]:
        recommendation = "🟢 <b>EXCELLENT</b> - Strategy siap untuk live trading!"
    elif grade in ["B+", "B"]:
        recommendation = "🟡 <b>GOOD</b> - Strategy profitable, pertimbangkan optimasi parameter"
    elif grade == "C":
        recommendation = "🟠 <b>FAIR</b> - Perlu improvement, test di timeframe lain"
    else:
        recommendation = "🔴 <b>POOR</b> - JANGAN live trading! Optimize strategy dulu"

    report += f"\n💡 <b>RECOMMENDATION</b>: {recommendation}\n"
    report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    return report
