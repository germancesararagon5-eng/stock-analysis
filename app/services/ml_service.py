import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.database import SessionLocal
from app.models import AnalysisResult
from app.core.debug import debug

logger = logging.getLogger(__name__)


def store_analysis_result(
    ticker: str,
    strategy: str,
    interval: str,
    period: int,
    signal: str,
    confidence: float,
    price: Optional[float] = None,
    indicators: Optional[dict] = None,
    reasons: Optional[list] = None,
    error: Optional[str] = None,
) -> int:
    ind = indicators or {}
    record = AnalysisResult(
        ticker=ticker.upper(),
        strategy=strategy,
        interval=interval,
        periods=period,
        signal=signal,
        confidence=confidence,
        price=price,
        rsi_14=ind.get("rsi_14"),
        ema_9=ind.get("ema_9"),
        ema_21=ind.get("ema_21"),
        ema_50=ind.get("ema_50"),
        ema_200=ind.get("ema_200"),
        bb_upper=ind.get("bb_upper"),
        bb_lower=ind.get("bb_lower"),
        macd=ind.get("macd"),
        macd_signal=ind.get("macd_signal"),
        macd_histogram=ind.get("macd_histogram"),
        volume=ind.get("volume"),
        atr=ind.get("atr"),
        support_1=ind.get("support_1"),
        resistance_1=ind.get("resistance_1"),
        indicators_json=ind,
        reasons=reasons or [],
        error=error,
    )
    db = SessionLocal()
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record.id
    except Exception as e:
        db.rollback()
        logger.warning("Failed to store analysis result: %s", e)
        return -1
    finally:
        db.close()


def resolve_outcomes(
    ticker: str,
    current_price: float,
    max_results: int = 100,
) -> int:
    db = SessionLocal()
    try:
        rows = (
            db.query(AnalysisResult)
            .filter(
                AnalysisResult.ticker == ticker.upper(),
                AnalysisResult.outcome.is_(None),
                AnalysisResult.signal.in_(["BUY", "SELL"]),
                AnalysisResult.price.isnot(None),
                AnalysisResult.error.is_(None),
            )
            .order_by(AnalysisResult.created_at.desc())
            .limit(max_results)
            .all()
        )
        resolved = 0
        for row in rows:
            if not row.price or row.price == 0:
                continue
            change = (current_price - row.price) / row.price * 100
            if row.signal == "SELL":
                change = -change
            if abs(change) >= 1.0:
                row.outcome = "WIN" if change > 0 else "LOSS"
            else:
                row.outcome = "PENDING"
            row.price_change_pct = round(change, 2)
            row.resolved_at = datetime.now(timezone.utc)
            resolved += 1
        if resolved:
            db.commit()
            logger.info("Resolved %d outcomes for %s", resolved, ticker)
        return resolved
    except Exception as e:
        db.rollback()
        logger.warning("Error resolving outcomes: %s", e)
        return 0
    finally:
        db.close()


def export_dataset(
    strategies: Optional[list[str]] = None,
    tickers: Optional[list[str]] = None,
    limit: int = 10000,
    min_confidence: float = 0.0,
) -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(AnalysisResult)
        if strategies:
            q = q.filter(AnalysisResult.strategy.in_(strategies))
        if tickers:
            q = q.filter(AnalysisResult.ticker.in_(tickers))
        q = q.filter(AnalysisResult.confidence >= min_confidence)
        q = q.order_by(AnalysisResult.created_at.desc()).limit(limit)
        rows = q.all()
        return [
            {
                "ticker": r.ticker,
                "strategy": r.strategy,
                "interval": r.interval,
                "signal": r.signal,
                "confidence": r.confidence,
                "price": r.price,
                "rsi_14": r.rsi_14,
                "ema_9": r.ema_9,
                "ema_21": r.ema_21,
                "ema_50": r.ema_50,
                "ema_200": r.ema_200,
                "bb_upper": r.bb_upper,
                "bb_lower": r.bb_lower,
                "macd": r.macd,
                "macd_signal": r.macd_signal,
                "macd_histogram": r.macd_histogram,
                "volume": r.volume,
                "atr": r.atr,
                "support_1": r.support_1,
                "resistance_1": r.resistance_1,
                "outcome": r.outcome,
                "price_change_pct": r.price_change_pct,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    finally:
        db.close()


def get_dataset_stats() -> dict:
    db = SessionLocal()
    try:
        total = db.query(AnalysisResult).count()
        with_outcome = db.query(AnalysisResult).filter(AnalysisResult.outcome.isnot(None)).count()
        win = db.query(AnalysisResult).filter(AnalysisResult.outcome == "WIN").count()
        loss = db.query(AnalysisResult).filter(AnalysisResult.outcome == "LOSS").count()
        by_strategy = {}
        for s in ["scalping", "swing", "momentum", "mean_reversion", "breakout", "market_structure"]:
            cnt = db.query(AnalysisResult).filter(AnalysisResult.strategy == s).count()
            if cnt:
                win_s = db.query(AnalysisResult).filter(
                    AnalysisResult.strategy == s, AnalysisResult.outcome == "WIN"
                ).count()
                by_strategy[s] = {"total": cnt, "win": win_s}
        return {
            "total_records": total,
            "with_outcome": with_outcome,
            "win": win,
            "loss": loss,
            "win_rate": round(win / (win + loss) * 100, 1) if (win + loss) > 0 else 0,
            "by_strategy": by_strategy,
        }
    finally:
        db.close()
