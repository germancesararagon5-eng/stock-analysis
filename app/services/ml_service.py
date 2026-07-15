import logging
from datetime import datetime, timezone
from typing import Optional

import numpy as np

from app.database import SessionLocal
from app.models import AnalysisResult

logger = logging.getLogger(__name__)

_MODEL = None
_MODEL_META = {}

FEATURE_COLS = [
    "rsi_14", "ema_9", "ema_21", "ema_50", "ema_200",
    "bb_upper", "bb_lower", "macd", "macd_signal", "macd_histogram",
    "volume", "atr", "support_1", "resistance_1", "confidence",
]


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


def _extract_features(row) -> list[float]:
    return [
        row.rsi_14 or 50.0,
        row.ema_9 or 0.0,
        row.ema_21 or 0.0,
        row.ema_50 or 0.0,
        row.ema_200 or 0.0,
        row.bb_upper or 0.0,
        row.bb_lower or 0.0,
        row.macd or 0.0,
        row.macd_signal or 0.0,
        row.macd_histogram or 0.0,
        row.volume or 0.0,
        row.atr or 0.0,
        row.support_1 or 0.0,
        row.resistance_1 or 0.0,
        row.confidence or 0.0,
    ]


def _features_from_dict(d: dict) -> list[float]:
    return [
        d.get("rsi_14", 50.0) or 50.0,
        d.get("ema_9", 0.0) or 0.0,
        d.get("ema_21", 0.0) or 0.0,
        d.get("ema_50", 0.0) or 0.0,
        d.get("ema_200", 0.0) or 0.0,
        d.get("bb_upper", 0.0) or 0.0,
        d.get("bb_lower", 0.0) or 0.0,
        d.get("macd", 0.0) or 0.0,
        d.get("macd_signal", 0.0) or 0.0,
        d.get("macd_histogram", 0.0) or 0.0,
        d.get("volume", 0.0) or 0.0,
        d.get("atr", 0.0) or 0.0,
        d.get("support_1", 0.0) or 0.0,
        d.get("resistance_1", 0.0) or 0.0,
        d.get("confidence", 0.0) or 0.0,
    ]


def get_model_status() -> dict:
    if _MODEL is None:
        return {"trained": False, "samples": 0, "features": FEATURE_COLS}
    return {
        "trained": True,
        "samples": _MODEL_META.get("samples", 0),
        "accuracy": _MODEL_META.get("accuracy"),
        "feature_importance": _MODEL_META.get("feature_importance"),
        "classes": _MODEL_META.get("classes", []),
        "features": FEATURE_COLS,
        "trained_at": _MODEL_META.get("trained_at"),
    }


def train_model() -> dict:
    global _MODEL, _MODEL_META
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
    from sklearn.model_selection import train_test_split

    db = SessionLocal()
    try:
        rows = (
            db.query(AnalysisResult)
            .filter(
                AnalysisResult.outcome.in_(["WIN", "LOSS"]),
                AnalysisResult.error.is_(None),
            )
            .all()
        )
        if len(rows) < 10:
            return {"error": f"Se necesitan al menos 10 muestras con outcome WIN/LOSS, se tienen {len(rows)}"}

        X = np.array([_extract_features(r) for r in rows])
        y = np.array([1 if r.outcome == "WIN" else 0 for r in rows])

        if len(np.unique(y)) < 2:
            return {"error": "Se necesitan al menos 2 clases (WIN y LOSS) en los datos"}

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        model = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42, class_weight="balanced"
        )
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        accuracy = float(accuracy_score(y_test, y_pred))

        cm = confusion_matrix(y_test, y_pred).tolist()
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

        importance = [
            {"feature": FEATURE_COLS[i], "importance": round(float(v), 4)}
            for i, v in enumerate(model.feature_importances_)
        ]
        importance.sort(key=lambda x: x["importance"], reverse=True)

        _MODEL = model
        _MODEL_META = {
            "samples": len(rows),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "accuracy": round(accuracy, 4),
            "confusion_matrix": cm,
            "classification_report": report,
            "feature_importance": importance,
            "classes": ["LOSS", "WIN"],
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            "ML model trained: accuracy=%.2f%%, samples=%d",
            accuracy * 100, len(rows),
        )

        return get_model_status()

    except Exception as e:
        logger.error("Error training ML model: %s", e)
        return {"error": str(e)}
    finally:
        db.close()


def predict_outcome(features: list[float]) -> dict:
    if _MODEL is None:
        return {"error": "Modelo no entrenado. Ejecute /api/ml/train primero."}

    try:
        X = np.array([features])
        proba = _MODEL.predict_proba(X)[0]
        pred = _MODEL.predict(X)[0]

        win_prob = float(proba[1]) if _MODEL.classes_[1] == 1 else float(proba[0])
        loss_prob = float(proba[0]) if _MODEL.classes_[0] == 0 else float(proba[1])

        return {
            "prediction": "WIN" if pred == 1 else "LOSS",
            "win_probability": round(win_prob, 4),
            "loss_probability": round(loss_prob, 4),
        }
    except Exception as e:
        logger.warning("Prediction error: %s", e)
        return {"error": str(e)}


def predict_from_indicators(indicators: dict) -> dict:
    features = _features_from_dict(indicators)
    return predict_outcome(features)


def backtest_comparison(
    ticker: str,
    interval: str = "1d",
    periods: int = 100,
) -> dict:
    from app.services.analysis_service import run_analysis

    if _MODEL is None:
        return {"error": "Modelo no entrenado. Ejecute /api/ml/train primero."}

    strategies = ["scalping", "swing", "momentum", "mean_reversion", "breakout", "market_structure"]
    results = []

    for strategy in strategies:
        try:
            r = run_analysis(
                ticker=ticker,
                strategy=strategy,
                interval=interval,
                periods=periods,
                store_prediction=False,
            )
            indicators = r.get("indicators", {})
            ml_result = predict_from_indicators(indicators)

            results.append({
                "strategy": strategy,
                "signal": r["signal"],
                "confidence": r["confidence"],
                "price": indicators.get("price"),
                "ml_prediction": ml_result.get("prediction", "N/A"),
                "ml_win_probability": ml_result.get("win_probability"),
                "agreement": (
                    "AGREE" if (
                        r["signal"] == "BUY" and ml_result.get("prediction") == "WIN"
                    ) or (
                        r["signal"] == "SELL" and ml_result.get("prediction") == "LOSS"
                    ) or (
                        r["signal"] == "NEUTRAL"
                    ) else "DISAGREE"
                ),
                "error": None,
            })
        except Exception as e:
            logger.warning("Backtest error for %s/%s: %s", ticker, strategy, e)
            results.append({
                "strategy": strategy,
                "signal": "ERROR",
                "confidence": 0.0,
                "price": None,
                "ml_prediction": "N/A",
                "ml_win_probability": None,
                "agreement": "N/A",
                "error": str(e),
            })

    agree_count = sum(1 for r in results if r["agreement"] == "AGREE")
    disagree_count = sum(1 for r in results if r["agreement"] == "DISAGREE")

    return {
        "ticker": ticker.upper(),
        "interval": interval,
        "model_trained": True,
        "model_accuracy": _MODEL_META.get("accuracy"),
        "results": results,
        "summary": {
            "total_strategies": len(results),
            "agree": agree_count,
            "disagree": disagree_count,
            "agreement_rate": round(agree_count / len(results) * 100, 1) if results else 0,
        },
    }
