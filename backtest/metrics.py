"""
Performance metrics calculation.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np


def calculate_metrics(trades: List[Dict], initial_balance: float, 
                       final_balance: float) -> Dict:
    """Calculate comprehensive performance metrics."""
    
    if not trades:
        return {}

    pnls = [t["pnl"] for t in trades]
    pnls_pct = [t["pnl_pct"] for t in trades]
    
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    
    total_pnl = sum(pnls)
    win_count = len(wins)
    loss_count = len(losses)
    total_trades = len(trades)
    
    winrate = (win_count / total_trades * 100) if total_trades > 0 else 0
    
    avg_win = np.mean(wins) if wins else 0
    avg_loss = np.mean(losses) if losses else 0
    
    # Profit Factor
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Risk/Reward
    rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    
    # Max Drawdown
    cumulative = np.cumsum(pnls)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = running_max - cumulative
    max_drawdown = float(np.max(drawdown)) if len(drawdown) > 0 else 0
    max_drawdown_pct = (max_drawdown / initial_balance) * 100
    
    # Return
    total_return_pct = ((final_balance - initial_balance) / initial_balance) * 100
    
    # Sharpe Ratio (annualized)
    if len(pnls_pct) > 1:
        returns_std = np.std(pnls_pct)
        sharpe = (np.mean(pnls_pct) / returns_std * np.sqrt(252)) if returns_std > 0 else 0
    else:
        sharpe = 0
    
    # Consecutive wins/losses
    max_consecutive_wins = _max_consecutive(trades, win=True)
    max_consecutive_losses = _max_consecutive(trades, win=False)
    
    # Expectancy
    expectancy = (winrate/100 * avg_win) + ((1 - winrate/100) * avg_loss)
    
    return {
        "total_trades": total_trades,
        "win_count": win_count,
        "loss_count": loss_count,
        "winrate": winrate,
        "total_pnl": total_pnl,
        "total_return_pct": total_return_pct,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "avg_rr": rr_ratio,
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown,
        "max_drawdown_pct": max_drawdown_pct,
        "sharpe_ratio": sharpe,
        "expectancy": expectancy,
        "max_consecutive_wins": max_consecutive_wins,
        "max_consecutive_losses": max_consecutive_losses,
        "best_trade": max(pnls),
        "worst_trade": min(pnls),
        "initial_balance": initial_balance,
        "final_balance": final_balance,
    }


def _max_consecutive(trades: List[Dict], win: bool = True) -> int:
    """Hitung max consecutive wins/losses."""
    max_streak = 0
    current = 0
    for t in trades:
        is_win = t["pnl"] > 0
        if is_win == win:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return max_streak
