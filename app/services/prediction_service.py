import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Prediction

logger = logging.getLogger(__name__)

INTERVAL_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "1d": 1440}


def store_prediction(
    ticker: str,
    signal: str,
    confidence: float,
    strategy: str = "scalping",
    interval: str = "5m",
    periods: int = 100,
    price: Optional[float] = None,
    reasons: Optional[list] = None,
    indicators: Optional[dict] = None,
) -> int:
    db: Session = SessionLocal()
    try:
        pred = Prediction(
            ticker=ticker,
            signal=signal,
            confidence=confidence,
            strategy=strategy,
            interval=interval,
            periods=periods,
            price_at_prediction=price,
            reasons=reasons or [],
            indicators_snapshot=indicators or {},
            outcome="PENDING",
        )
        db.add(pred)
        db.commit()
        db.refresh(pred)
        logger.info("Prediction stored: %s %s %.0f%%", ticker, signal, confidence * 100)
        return pred.id
    except Exception as e:
        logger.error("Error storing prediction: %s", e)
        db.rollback()
        return -1
    finally:
        db.close()


def resolve_predictions(count: int = 50) -> int:
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        def min_age_for_interval(interval: str) -> timedelta:
            mins = INTERVAL_MINUTES.get(interval, 5)
            return timedelta(minutes=max(1, min(mins, 60)))

        pending = (
            db.query(Prediction)
            .filter(Prediction.outcome == "PENDING")
            .filter(Prediction.created_at < now - timedelta(minutes=1))
            .order_by(Prediction.created_at.asc())
            .limit(count)
            .all()
        )
        resolved = 0
        for pred in pending:
            age_limit = min_age_for_interval(pred.interval or "5m")
            if pred.created_at and pred.created_at > now - age_limit:
                logger.info(
                    "Prediction %d %s too young (age=%s, min=%s)",
                    pred.id, pred.ticker,
                    (now - pred.created_at) if pred.created_at else "?",
                    age_limit,
                )
                continue
            try:
                from app.services.analysis_service import run_analysis

                result = run_analysis(
                    ticker=pred.ticker,
                    strategy=pred.strategy,
                    interval=pred.interval,
                    periods=max(pred.periods or 100, 20),
                )
                current_price = result.get("indicators", {}).get("price")
                if current_price is None or pred.price_at_prediction is None:
                    continue

                change_pct = ((current_price - pred.price_at_prediction) / pred.price_at_prediction) * 100
                pred.price_at_outcome = current_price
                pred.price_change_pct = round(change_pct, 2)
                pred.resolved_at = datetime.now(timezone.utc)

                if pred.signal == "BUY":
                    pred.outcome = "CORRECT" if change_pct > 0 else "INCORRECT"
                elif pred.signal == "SELL":
                    pred.outcome = "CORRECT" if change_pct < 0 else "INCORRECT"
                else:
                    pred.outcome = "NEUTRAL"

                logger.info(
                    "Prediction %d resolved: %s (%+.2f%%)",
                    pred.id, pred.outcome, change_pct,
                )
                resolved += 1
            except Exception as e:
                logger.warning("Error resolving prediction %d: %s", pred.id, e)

        db.commit()
        return resolved
    except Exception as e:
        logger.error("Error resolving predictions: %s", e)
        db.rollback()
        return 0
    finally:
        db.close()


def get_prediction_stats(ticker: Optional[str] = None) -> dict:
    db: Session = SessionLocal()
    try:
        q = db.query(Prediction)
        if ticker:
            q = q.filter(Prediction.ticker == ticker.upper())
        total = q.count()
        resolved = q.filter(Prediction.outcome.in_(["CORRECT", "INCORRECT"])).count()
        correct = q.filter(Prediction.outcome == "CORRECT").count()
        pending = q.filter(Prediction.outcome == "PENDING").count()

        accuracy = round((correct / resolved * 100), 1) if resolved > 0 else 0.0

        return {
            "total": total,
            "resolved": resolved,
            "correct": correct,
            "pending": pending,
            "accuracy_pct": accuracy,
        }
    finally:
        db.close()


def get_predictions(
    ticker: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    db: Session = SessionLocal()
    try:
        q = db.query(Prediction).order_by(Prediction.created_at.desc())
        if ticker:
            q = q.filter(Prediction.ticker == ticker.upper())
        rows = q.offset(offset).limit(limit).all()
        return [
            {
                "id": r.id,
                "ticker": r.ticker,
                "signal": r.signal,
                "confidence": r.confidence,
                "strategy": r.strategy,
                "interval": r.interval,
                "price_at_prediction": r.price_at_prediction,
                "reasons": r.reasons,
                "outcome": r.outcome or "PENDING",
                "price_at_outcome": r.price_at_outcome,
                "price_change_pct": r.price_change_pct,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
            }
            for r in rows
        ]
    finally:
        db.close()
