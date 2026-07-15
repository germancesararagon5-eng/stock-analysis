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
    db: Session = None
    try:
        db = SessionLocal()
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
        if db is not None:
            db.rollback()
        return -1
    finally:
        if db is not None:
            db.close()


DEFAULT_THRESHOLD_PCT = 0.0  # Minimum price change % to consider correct


def resolve_predictions(count: int = 50, threshold_pct: float = DEFAULT_THRESHOLD_PCT) -> int:
    db: Session = None
    try:
        db = SessionLocal()
        now = datetime.now(timezone.utc).replace(tzinfo=None)

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
                pred.resolved_at = now

                meets_threshold = abs(change_pct) >= threshold_pct

                if pred.signal == "BUY":
                    pred.outcome = "CORRECT" if change_pct > 0 and meets_threshold else "INCORRECT"
                    pred.pnl = round(current_price - pred.price_at_prediction, 2)
                elif pred.signal == "SELL":
                    pred.outcome = "CORRECT" if change_pct < 0 and meets_threshold else "INCORRECT"
                    pred.pnl = round(pred.price_at_prediction - current_price, 2)
                else:
                    pred.outcome = "NEUTRAL"
                    pred.pnl = 0.0

                pred.pnl_pct = round(pred.pnl / pred.price_at_prediction * 100, 2) if pred.price_at_prediction else 0.0

                logger.info(
                    "Prediction %d resolved: %s (%+.2f%%, PnL=%+.2f)",
                    pred.id, pred.outcome, change_pct, pred.pnl or 0,
                )
                resolved += 1
            except Exception as e:
                logger.warning("Error resolving prediction %d: %s", pred.id, e)

        db.commit()
        return resolved
    except Exception as e:
        logger.error("Error resolving predictions: %s", e)
        if db is not None:
            db.rollback()
        return 0
    finally:
        if db is not None:
            db.close()


def get_prediction_stats(ticker: Optional[str] = None) -> dict:
    db = None
    try:
        db = SessionLocal()
        q = db.query(Prediction)
        if ticker:
            q = q.filter(Prediction.ticker == ticker.upper())
        total = q.count()
        resolved_q = q.filter(Prediction.outcome.in_(["CORRECT", "INCORRECT"]))
        resolved = resolved_q.count()
        correct = q.filter(Prediction.outcome == "CORRECT").count()
        pending = q.filter(Prediction.outcome == "PENDING").count()
        accuracy = round((correct / resolved * 100), 1) if resolved > 0 else 0.0

        total_pnl = 0.0
        for r in resolved_q.all():
            if r.pnl is not None:
                total_pnl += r.pnl
        total_pnl = round(total_pnl, 2)

        winning_trades = q.filter(Prediction.outcome == "CORRECT").count()
        losing_trades = q.filter(Prediction.outcome == "INCORRECT").count()

        return {
            "total": total,
            "resolved": resolved,
            "correct": correct,
            "pending": pending,
            "accuracy_pct": accuracy,
            "total_pnl": total_pnl,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
        }
    finally:
        if db is not None:
            db.close()


def get_trading_summary(ticker: Optional[str] = None) -> dict:
    db = None
    try:
        db = SessionLocal()
        q = db.query(Prediction).filter(Prediction.outcome.in_(["CORRECT", "INCORRECT"]))
        if ticker:
            q = q.filter(Prediction.ticker == ticker.upper())

        rows = q.order_by(Prediction.created_at.desc()).limit(1000).all()
        total_pnl = 0.0
        wins = 0
        losses = 0
        total_win_pnl = 0.0
        total_loss_pnl = 0.0
        trades = []

        for r in rows:
            pnl_val = r.pnl or 0.0
            total_pnl += pnl_val
            if r.outcome == "CORRECT":
                wins += 1
                total_win_pnl += pnl_val
            else:
                losses += 1
                total_loss_pnl += pnl_val

            trades.append({
                "id": r.id,
                "ticker": r.ticker,
                "signal": r.signal,
                "confidence": r.confidence,
                "entry_price": r.price_at_prediction,
                "exit_price": r.price_at_outcome,
                "pnl": pnl_val,
                "pnl_pct": r.pnl_pct,
                "outcome": r.outcome,
                "strategy": r.strategy,
                "interval": r.interval,
                "entered_at": r.created_at.isoformat() if r.created_at else None,
                "exited_at": r.resolved_at.isoformat() if r.resolved_at else None,
            })

        total = wins + losses
        win_rate = round((wins / total * 100), 1) if total > 0 else 0.0
        avg_win = round(total_win_pnl / wins, 2) if wins > 0 else 0.0
        avg_loss = round(total_loss_pnl / losses, 2) if losses > 0 else 0.0

        return {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate_pct": win_rate,
            "total_pnl": round(total_pnl, 2),
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": round(abs(total_win_pnl / total_loss_pnl), 2) if total_loss_pnl != 0 else 0.0,
            "trades": trades[:50],
        }
    finally:
        if db is not None:
            db.close()


def get_predictions(
    ticker: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    db = None
    try:
        db = SessionLocal()
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
                "pnl": r.pnl,
                "pnl_pct": r.pnl_pct,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
            }
            for r in rows
        ]
    finally:
        if db is not None:
            db.close()
