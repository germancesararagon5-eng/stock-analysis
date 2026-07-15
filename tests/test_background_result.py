from datetime import datetime, timezone

from app.models import BackgroundResult


def _count_results(db) -> int:
    return db.query(BackgroundResult).count()


def test_create_background_result(db_session):
    result = BackgroundResult(
        ticker="AAPL",
        signal="BUY",
        confidence=0.85,
        price=150.0,
        strategy="scalping",
        interval="5m",
        periods=100,
    )
    db_session.add(result)
    db_session.commit()

    saved = db_session.query(BackgroundResult).first()
    assert saved.ticker == "AAPL"
    assert saved.signal == "BUY"
    assert saved.confidence == 0.85
    assert saved.price == 150.0
    assert saved.strategy == "scalping"
    assert saved.interval == "5m"
    assert saved.periods == 100
    assert saved.error is None
    assert saved.created_at is not None


def test_background_result_nullable_fields(db_session):
    result = BackgroundResult(
        ticker="MSFT",
        signal="SELL",
        confidence=0.0,
    )
    db_session.add(result)
    db_session.commit()

    saved = db_session.query(BackgroundResult).first()
    assert saved.ticker == "MSFT"
    assert saved.signal == "SELL"
    assert saved.price is None
    assert saved.strategy == "scalping"
    assert saved.interval == "5m"
    assert saved.periods == 100
    assert saved.error is None


def test_background_result_with_error(db_session):
    result = BackgroundResult(
        ticker="ERR",
        signal="ERROR",
        confidence=0.0,
        error="Network failure",
    )
    db_session.add(result)
    db_session.commit()

    saved = db_session.query(BackgroundResult).first()
    assert saved.signal == "ERROR"
    assert saved.error == "Network failure"


def test_background_result_auto_timestamp(db_session):
    before = datetime.now(timezone.utc)
    result = BackgroundResult(ticker="TSLA", signal="BUY", confidence=0.5)
    db_session.add(result)
    db_session.commit()
    after = datetime.now(timezone.utc)

    saved = db_session.query(BackgroundResult).first()
    assert saved.created_at is not None
    ts = saved.created_at.replace(tzinfo=timezone.utc).timestamp()
    # SQLite stores second precision; give 2s tolerance
    assert before.timestamp() - 2 <= ts <= after.timestamp() + 2


def test_background_result_multiple_results(db_session):
    for i, ticker in enumerate(["AAPL", "MSFT", "GOOGL"]):
        db_session.add(BackgroundResult(
            ticker=ticker,
            signal="BUY",
            confidence=0.5 + i * 0.1,
            price=100.0 + i * 10,
            strategy="swing",
        ))
    db_session.commit()

    results = db_session.query(BackgroundResult).order_by(BackgroundResult.confidence.desc()).all()
    assert len(results) == 3
    assert results[0].ticker == "GOOGL"
    assert results[0].confidence == 0.7


def test_background_result_delete(db_session):
    r = BackgroundResult(ticker="TEMP", signal="BUY", confidence=0.5)
    db_session.add(r)
    db_session.commit()
    assert _count_results(db_session) == 1

    db_session.delete(r)
    db_session.commit()
    assert _count_results(db_session) == 0


def test_background_result_index_on_ticker(db_session):
    db_session.add_all([
        BackgroundResult(ticker="AAPL", signal="BUY", confidence=0.8),
        BackgroundResult(ticker="AAPL", signal="SELL", confidence=0.6),
        BackgroundResult(ticker="MSFT", signal="BUY", confidence=0.7),
    ])
    db_session.commit()

    aapl_results = db_session.query(BackgroundResult).filter(BackgroundResult.ticker == "AAPL").all()
    assert len(aapl_results) == 2
