"""
Configuration management dengan Pydantic v2.
Validasi ketat untuk production safety.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExchangeSettings(BaseSettings):
    name: str = "binance"
    api_key: str = ""
    secret: str = ""
    passphrase: str = ""
    testnet: bool = True
    rate_limit: int = 1200
    timeout: int = 30000

    model_config = SettingsConfigDict(env_prefix="EXCHANGE_", case_sensitive=False)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        supported = ["binance", "bybit", "okx", "bitget", "kucoin"]
        if v.lower() not in supported:
            raise ValueError(f"Exchange '{v}' not supported. Use: {supported}")
        return v.lower()


class TelegramSettings(BaseSettings):
    bot_token: str = ""
    admin_ids: List[int] = []
    channel_id: Optional[int] = None
    log_chat_id: Optional[int] = None

    model_config = SettingsConfigDict(env_prefix="TELEGRAM_", case_sensitive=False)

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_ids(cls, v):
        if isinstance(v, str):
            if not v:
                return []
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v or []


class TradingSettings(BaseSettings):
    symbol: str = "BTC/USDT"
    timeframe: str = "15m"
    timeframes_higher: List[str] = ["1h", "4h"]
    leverage: int = Field(default=5, ge=1, le=125)

    max_position_pct: float = Field(default=0.10, ge=0.01, le=1.0)
    risk_per_trade: float = Field(default=0.01, gt=0.0, le=0.10)
    max_open_trades: int = Field(default=2, ge=1, le=10)
    max_daily_trades: int = Field(default=10, ge=1)
    max_daily_loss_pct: float = Field(default=0.03, gt=0.0, le=0.20)
    max_drawdown_pct: float = Field(default=0.15, gt=0.0, le=0.50)

    stop_loss_atr_mult: float = Field(default=1.5, gt=0.0)
    take_profit_atr_mult: float = Field(default=2.5, gt=0.0)
    trailing_stop_pct: float = Field(default=0.015, gt=0.0, le=0.10)
    trailing_activation_pct: float = Field(default=0.02, gt=0.0)
    min_risk_reward: float = Field(default=1.8, ge=1.0)

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False, extra="ignore")

    @field_validator("timeframe")
    @classmethod
    def validate_timeframe(cls, v: str) -> str:
        valid = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        if v not in valid:
            raise ValueError(f"Invalid timeframe: {v}")
        return v

    @field_validator("timeframes_higher", mode="before")
    @classmethod
    def parse_timeframes(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v


class AISettings(BaseSettings):
    """AI Configuration dengan Groq support."""
    mode: Literal["technical", "hybrid", "technical_only"] = "hybrid"

    # Layer 1: Technical (always on)
    use_technical: bool = True
    use_sentiment_fng: bool = True
    use_sentiment_funding: bool = True

    # Layer 2: Groq (optional)
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"
    groq_timeout: int = 10
    groq_cache_ttl: int = 300  # 5 min cache

    # News source (optional)
    cryptopanic_api_key: str = ""
    use_news_api: bool = False
    fng_api_url: str = "https://api.alternative.me/fng/"

    # Thresholds
    confidence_threshold: float = Field(default=0.70, ge=0.0, le=1.0)
    min_signal_strength: float = Field(default=0.65, ge=0.0, le=1.0)
    htf_alignment_required: bool = True

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False, extra="ignore")

    @field_validator("mode", mode="before")
    @classmethod
    def normalize_mode(cls, v):
        if isinstance(v, str):
            v = v.lower().strip()
        if v == "technical_only":
            return "technical"
        return v

    @property
    def has_groq(self) -> bool:
        """Check if Groq is available."""
        return bool(self.groq_api_key) and self.mode == "hybrid"

    @property
    def effective_mode(self) -> str:
        """Get effective AI mode."""
        if self.mode == "hybrid" and not self.groq_api_key:
            return "technical (groq fallback)"
        return self.mode


class DatabaseSettings(BaseSettings):
    url: str = "sqlite+aiosqlite:///data/trading_bot.db"
    echo: bool = False

    model_config = SettingsConfigDict(env_prefix="DATABASE_", case_sensitive=False)


class NotificationSettings(BaseSettings):
    enabled: bool = True
    on_trade: bool = True
    on_signal: bool = True
    on_error: bool = True
    on_daily_summary: bool = True

    model_config = SettingsConfigDict(env_prefix="NOTIFY_", case_sensitive=False)


class MonitoringSettings(BaseSettings):
    health_check: int = 300
    position_check: int = 10
    scan: int = 60

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False, extra="ignore")


class AppSettings(BaseSettings):
    env: Literal["development", "production"] = "development"
    debug: bool = False

    exchange: ExchangeSettings = Field(default_factory=ExchangeSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    trading: TradingSettings = Field(default_factory=TradingSettings)
    ai: AISettings = Field(default_factory=AISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def validate_for_production(self) -> None:
        """Validate config untuk production use."""
        errors = []
        if self.env == "production":
            if self.exchange.testnet:
                errors.append("❌ Cannot use testnet in production!")
            if not self.exchange.api_key or not self.exchange.secret:
                errors.append("❌ Exchange API keys required for production!")
            if not self.telegram.bot_token:
                errors.append("❌ Telegram bot token required!")
            if not self.telegram.admin_ids:
                errors.append("❌ At least one Telegram admin ID required!")
        if errors:
            raise ValueError("Config validation failed:\n" + "\n".join(errors))


@lru_cache()
def get_settings() -> AppSettings:
    return AppSettings()


settings = get_settings()
