"""
AI Orchestrator - Combine Layer 1 (Technical) + Layer 2 (Groq).
"""
from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

from ai.signal_generator import SignalGenerator
from ai.sentiment_analyzer import SentimentAnalyzer
from ai.groq_analyzer import GroqAnalyzer
from config import settings
from utils.logger import logger


class AIOrchestrator:
    """
    Main AI orchestrator.
    Combines technical + sentiment + Groq LLM.
    """

    def __init__(self):
        self.signal_generator = SignalGenerator()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.groq_analyzer = GroqAnalyzer()
        logger.info(f"🤖 AI Mode: {settings.ai.effective_mode}")

    async def initialize(self):
        await self.sentiment_analyzer.init()

    async def close(self):
        await self.sentiment_analyzer.close()
        await self.groq_analyzer.close()

    async def analyze(self, df: pd.DataFrame, exchange=None, symbol: str = "BTC/USDT") -> Dict:
        """
        Full AI analysis pipeline.
        Returns complete signal dict.
        """
        # Layer 1: Sentiment
        sentiment = await self.sentiment_analyzer.get_overall_sentiment(exchange, symbol)

        # Layer 1: Technical signal
        signal = await self.signal_generator.generate_signal(df, sentiment)

        # Set AI mode
        signal["ai_mode"] = settings.ai.effective_mode

        # Layer 2: Groq enhancement (if enabled & signal not neutral)
        if self.groq_analyzer.enabled and signal["type"] != "neutral":
            signal = await self.groq_analyzer.enhance_signal(signal, symbol.split("/")[0])
        else:
            signal["ai_reasoning"] = "Technical analysis only"

        return signal

    async def quick_scan(self, exchange=None, symbol: str = "BTC/USDT") -> Dict:
        """Quick market scan without full signal generation."""
        sentiment = await self.sentiment_analyzer.get_overall_sentiment(exchange, symbol)
        groq_data = None
        if self.groq_analyzer.enabled:
            groq_data = await self.groq_analyzer.analyze_news_sentiment(symbol.split("/")[0])
        return {
            "sentiment": sentiment,
            "groq": groq_data,
            "ai_mode": settings.ai.effective_mode,
        }
