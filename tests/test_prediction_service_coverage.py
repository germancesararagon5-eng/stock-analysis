from unittest.mock import patch

from app.services.prediction_service import (
    get_prediction_stats,
    get_predictions,
    get_trading_summary,
    resolve_predictions,
    store_prediction,
)


def test_store_prediction_null_price():
    pred_id = store_prediction(
        ticker="NULLPRICE", signal="BUY", confidence=0.5,
        price=None, reasons=None, indicators=None,
    )
    assert pred_id > 0
    preds = get_predictions(ticker="NULLPRICE")
    assert len(preds) >= 1


def test_store_prediction_empty_reasons():
    pred_id = store_prediction(
        ticker="EMPTYREAS", signal="SELL", confidence=0.7,
        price=100.0, reasons=[], indicators={},
    )
    assert pred_id > 0


def test_store_prediction_db_error():
    with patch("app.services.prediction_service.SessionLocal") as m:
        m.side_effect = Exception("DB error")
        pred_id = store_prediction(
            ticker="DBERR", signal="BUY", confidence=0.5,
        )
        assert pred_id == -1


def test_get_predictions_limit_offset():
    for i in range(3):
        store_prediction(
            ticker="PAGING", signal="BUY", confidence=0.5,
            price=float(100 + i),
        )
    preds = get_predictions(ticker="PAGING", limit=2, offset=0)
    assert len(preds) <= 2


def test_get_prediction_stats_zero():
    stats = get_prediction_stats(ticker="NONEXISTENT_TICKER_XYZ")
    assert stats["total"] == 0
    assert stats["accuracy_pct"] == 0.0


def test_get_prediction_stats_with_data():
    store_prediction(
        ticker="STATSTR", signal="BUY", confidence=0.8,
        price=150.0,
    )
    stats = get_prediction_stats(ticker="STATSTR")
    assert stats["total"] >= 1
    assert "accuracy_pct" in stats
    assert "total_pnl" in stats


def test_get_trading_summary_empty():
    summary = get_trading_summary(ticker="NONEXISTENT_XYZ_123")
    assert summary["total_trades"] == 0
    assert summary["win_rate_pct"] == 0.0
    assert summary["profit_factor"] == 0.0


def test_resolve_predictions_db_error():
    with patch("app.services.prediction_service.SessionLocal") as m:
        m.side_effect = Exception("DB error")
        result = resolve_predictions(count=5)
        assert result == 0


def test_resolve_predictions_with_runtime_error():
    store_prediction(
        ticker="RESERR", signal="BUY", confidence=0.7,
        strategy="scalping", interval="1d", periods=100,
        price=100.0,
    )
    with patch("app.services.analysis_service.run_analysis") as mock_run:
        mock_run.side_effect = Exception("Network error")
        resolved = resolve_predictions(count=5)
        assert isinstance(resolved, int)


def test_store_prediction_all_intervals():
    for interval in ("1m", "5m", "15m", "1h", "1d"):
        pred_id = store_prediction(
            ticker="INTV", signal="BUY", confidence=0.5,
            interval=interval, price=100.0,
        )
        assert pred_id > 0


def test_pnl_calculation():
    pred_id = store_prediction(
        ticker="PNLCALC", signal="BUY", confidence=0.8,
        strategy="scalping", interval="1d", periods=100,
        price=100.0,
    )
    assert pred_id > 0
    summary = get_trading_summary(ticker="PNLCALC")
    assert "total_pnl" in summary
    assert "trades" in summary


def test_get_trading_summary_filter():
    store_prediction(
        ticker="TRADEFILT", signal="SELL", confidence=0.6,
        price=200.0,
    )
    summary = get_trading_summary(ticker="TRADEFILT")
    assert isinstance(summary["trades"], list)
    if summary["trades"]:
        t = summary["trades"][0]
        assert "entry_price" in t
        assert "exit_price" in t
        assert "pnl_pct" in t


# ═══════════════════════════════════════════════════════════════
# COVERAGE GAPS: resolve_predictions resolution logic
# ═══════════════════════════════════════════════════════════════
# We bypass the 1-minute age filter by inserting predictions
# directly with a past created_at.

def _past_prediction(db_session, ticker, signal, price, strategy="scalping", interval="5m"):
    """Insert a prediction with a past created_at using raw SQL to avoid tz issues."""
    from datetime import datetime, timedelta

    from app.models import Prediction
    p = Prediction(
        ticker=ticker, signal=signal, confidence=0.8,
        strategy=strategy, interval=interval, periods=100,
        price_at_prediction=float(price),
        outcome="PENDING",
    )
    db_session.add(p)
    db_session.commit()
    # Override created_at via SQL to guarantee a past naive timestamp
    past = datetime.utcnow() - timedelta(minutes=5)
    db_session.execute(
        __import__("sqlalchemy").text("UPDATE predictions SET created_at = :ts WHERE id = :id"),
        {"ts": past, "id": p.id},
    )
    db_session.commit()
    db_session.refresh(p)
    return p.id


def test_resolve_buy_correct(db_session):
    """BUY signal + price goes up → CORRECT."""
    from unittest.mock import patch

    _past_prediction(db_session, "RESBUY", "BUY", 100.0)

    with patch("app.services.analysis_service.run_analysis") as mock_run:
        mock_run.return_value = {"indicators": {"price": 105.0}}
        resolved = resolve_predictions(count=5)
        assert resolved >= 1

    stats = get_prediction_stats(ticker="RESBUY")
    assert stats["correct"] == 1
    assert stats["total_pnl"] > 0


def test_resolve_buy_incorrect(db_session):
    """BUY signal + price goes down → INCORRECT."""
    from unittest.mock import patch

    _past_prediction(db_session, "RESBUY2", "BUY", 100.0)

    with patch("app.services.analysis_service.run_analysis") as mock_run:
        mock_run.return_value = {"indicators": {"price": 95.0}}
        resolved = resolve_predictions(count=5)
        assert resolved >= 1

    stats = get_prediction_stats(ticker="RESBUY2")
    assert stats["correct"] == 0


def test_resolve_sell_correct(db_session):
    """SELL signal + price goes down → CORRECT."""
    from unittest.mock import patch

    _past_prediction(db_session, "RESSELL", "SELL", 100.0)

    with patch("app.services.analysis_service.run_analysis") as mock_run:
        mock_run.return_value = {"indicators": {"price": 90.0}}
        resolved = resolve_predictions(count=5)
        assert resolved >= 1

    stats = get_prediction_stats(ticker="RESSELL")
    assert stats["correct"] == 1


def test_resolve_neutral_outcome(db_session):
    """NEUTRAL signal always gets outcome='NEUTRAL' and pnl=0.0."""
    from unittest.mock import patch

    _past_prediction(db_session, "RESNEUT", "NEUTRAL", 100.0)

    with patch("app.services.analysis_service.run_analysis") as mock_run:
        mock_run.return_value = {"indicators": {"price": 105.0}}
        resolved = resolve_predictions(count=5)
        assert resolved >= 1

    stats = get_prediction_stats(ticker="RESNEUT")
    assert stats["total"] == 1
    assert stats["pending"] == 0


def test_resolve_skips_when_no_price(db_session):
    """resolve_predictions skips prediction when run_analysis returns no price."""
    from unittest.mock import patch

    _past_prediction(db_session, "RESNOPR", "BUY", 100.0)

    with patch("app.services.analysis_service.run_analysis") as mock_run:
        mock_run.return_value = {"indicators": {}}
        resolved = resolve_predictions(count=5)
        assert resolved == 0


def test_resolve_with_threshold_not_met(db_session):
    """resolve_predictions respects threshold_pct."""
    from unittest.mock import patch

    _past_prediction(db_session, "RESTHR", "BUY", 100.0)

    with patch("app.services.analysis_service.run_analysis") as mock_run:
        mock_run.return_value = {"indicators": {"price": 100.5}}
        resolved = resolve_predictions(count=5, threshold_pct=1.0)
        assert resolved >= 1
        stats = get_prediction_stats(ticker="RESTHR")
        assert stats["correct"] == 0, "0.5% < 1% threshold → should NOT be correct"


def test_store_prediction_db_rollback():
    """store_prediction rollback path when commit fails."""
    from unittest.mock import patch

    with patch("app.services.prediction_service.SessionLocal") as m:
        mock_session = m.return_value
        mock_session.commit.side_effect = Exception("Commit failed")
        pred_id = store_prediction(ticker="ROLLBACK", signal="BUY", confidence=0.5)
        assert pred_id == -1
        mock_session.rollback.assert_called_once()


def test_resolve_predictions_db_rollback():
    """resolve_predictions outer rollback path."""
    from unittest.mock import patch

    with patch("app.services.prediction_service.SessionLocal") as m:
        mock_session = m.return_value
        mock_session.query.side_effect = Exception("Query failed")
        result = resolve_predictions(count=5)
        assert result == 0
        mock_session.rollback.assert_called_once()


def test_get_prediction_stats_pnl_accumulation(db_session):
    """get_prediction_stats accumulates PnL correctly."""
    from unittest.mock import patch

    _past_prediction(db_session, "PNLSTATS", "BUY", 100.0)
    _past_prediction(db_session, "PNLSTATS", "BUY", 50.0)

    with patch("app.services.analysis_service.run_analysis") as mock_run:
        mock_run.return_value = {"indicators": {"price": 110.0}}
        resolve_predictions(count=10)

    stats = get_prediction_stats(ticker="PNLSTATS")
    assert stats["total_pnl"] > 0


def test_get_trading_summary_with_resolved(db_session):
    """get_trading_summary returns win/loss breakdown with resolved predictions."""
    from unittest.mock import patch

    _past_prediction(db_session, "TRADESUM", "BUY", 100.0)
    _past_prediction(db_session, "TRADESUM", "SELL", 50.0)

    with patch("app.services.analysis_service.run_analysis") as mock_run:
        mock_run.return_value = {"indicators": {"price": 110.0}}
        resolve_predictions(count=10)

    summary = get_trading_summary(ticker="TRADESUM")
    assert summary["total_trades"] >= 1
    assert "profit_factor" in summary
    assert "avg_win" in summary
    assert "avg_loss" in summary
