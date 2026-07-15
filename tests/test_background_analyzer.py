import threading
import threading
import time
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from app.services.background_analyzer import BackgroundAnalyzer, background_analyzer


# ── Fixtures ──

@pytest.fixture
def analyzer():
    return BackgroundAnalyzer()


def fake_run_analysis(**kwargs):
    return {
        "signal": "BUY",
        "confidence": 0.85,
        "indicators": {"price": 150.0, "ema_9": [149, 150], "ema_21": [148, 149]},
        "reasons": ["Test reason"],
    }


# ── Initialization / config ──

class TestInitAndConfig:
    def test_default_config(self, analyzer):
        cfg = analyzer._default_config()
        assert not cfg["enabled"]
        assert cfg["tickers"] == []
        assert cfg["strategy"] == "all"
        assert cfg["interval"] == "1d"
        assert cfg["periods"] == 100
        assert cfg["min_confidence"] == 0.0
        assert cfg["run_every_seconds"] == 3600

    def test_get_config(self, analyzer):
        cfg = analyzer.get_config()
        assert "enabled" in cfg
        assert "max_results" not in cfg

    def test_update_config(self, analyzer):
        analyzer.update_config({"strategy": "scalping", "interval": "1d"})
        cfg = analyzer.get_config()
        assert cfg["strategy"] == "scalping"
        assert cfg["interval"] == "1d"

    def test_update_config_rejects_invalid_keys(self, analyzer):
        analyzer.update_config({"invalid_key": "value"})
        cfg = analyzer.get_config()
        assert "invalid_key" not in cfg


# ── Start / Stop ──

class TestStartStop:
    def test_start(self, analyzer):
        with patch.object(analyzer, "_thread") as mock_thread:
            mock_thread.is_alive.return_value = False
            result = analyzer.start()
            assert result == {"status": "started"}
            assert analyzer._config["enabled"]

    def test_start_already_running(self, analyzer):
        analyzer._config["enabled"] = True
        result = analyzer.start()
        assert result == {"status": "already_running"}

    def test_stop(self, analyzer):
        analyzer._config["enabled"] = True
        with patch.object(analyzer, "_thread") as mock_thread:
            mock_thread.is_alive.return_value = True
            result = analyzer.stop()
            assert result == {"status": "stopped"}
            assert not analyzer._config["enabled"]

    def test_stop_already_stopped(self, analyzer):
        result = analyzer.stop()
        assert result == {"status": "already_stopped"}

    def test_update_config_restarts_when_enabled(self, analyzer):
        analyzer._config["enabled"] = True
        with (
            patch.object(analyzer, "_thread") as mock_thread,
            patch("threading.Thread") as mock_thread_cls,
        ):
            mock_thread.is_alive.return_value = True
            mock_new = MagicMock()
            mock_thread_cls.return_value = mock_new
            analyzer.update_config({"strategy": "scalping"})
            mock_thread_cls.assert_called_once()
            mock_new.start.assert_called_once()


# ── Results ──

class TestGetResults:
    def test_get_results_from_db(self, analyzer):
        mock_record = MagicMock()
        mock_record.ticker = "AAPL"
        mock_record.signal = "BUY"
        mock_record.confidence = 0.85
        mock_record.price = 150.0
        mock_record.strategy = "scalping"
        mock_record.interval = "5m"
        mock_record.periods = 100
        mock_record.error = None
        mock_record.created_at = MagicMock()
        mock_record.created_at.isoformat.return_value = "2026-01-01T00:00:00"

        with patch("app.services.background_analyzer.SessionLocal") as mock_sl:
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_query = mock_session.query.return_value
            mock_order = mock_query.order_by.return_value
            mock_order.limit.return_value.all.return_value = [mock_record]

            results = analyzer.get_results(limit=10)
            assert len(results) == 1
            assert results[0]["ticker"] == "AAPL"

    def test_get_results_db_error_fallback(self, analyzer):
        mock_in_mem = {"ticker": "FALLBACK", "signal": "BUY", "confidence": 0.5}
        analyzer._results = [mock_in_mem]

        with patch("app.services.background_analyzer.SessionLocal") as mock_sl:
            mock_sl.side_effect = Exception("DB error")
            results = analyzer.get_results(limit=10)
            assert len(results) == 1
            assert results[0]["ticker"] == "FALLBACK"

    def test_get_results_skips_errors(self, analyzer):
        mock_ok = MagicMock()
        mock_ok.ticker = "AAPL"
        mock_ok.signal = "BUY"
        mock_ok.confidence = 0.85
        mock_ok.price = 150.0
        mock_ok.strategy = "scalping"
        mock_ok.interval = "5m"
        mock_ok.periods = 100
        mock_ok.error = None
        mock_ok.created_at = MagicMock()
        mock_ok.created_at.isoformat.return_value = "2026-01-01T00:00:00"

        mock_err = MagicMock()
        mock_err.error = "fail"

        with patch("app.services.background_analyzer.SessionLocal") as mock_sl:
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_ok, mock_err]
            results = analyzer.get_results(limit=10)
            assert len(results) == 1


# ── _run_cycle ──

class TestRunCycle:
    def test_default_tickers_when_empty(self, analyzer):
        analyzer._config["tickers"] = []
        n_strategies = 6
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.resolve_predictions", return_value=0),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            # Default tickers (21) x 6 strategies = 126 results
            expected = len(analyzer._default_config()["tickers"]) or 21 * n_strategies
            assert len(analyzer._results) == 21 * n_strategies

    def test_stores_prediction_when_above_confidence(self, analyzer):
        analyzer._config["tickers"] = ["AAPL"]
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction") as mock_store,
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.resolve_predictions", return_value=0),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            # 1 ticker x 6 strategies = 6 calls to store_prediction (if all are BUY/SELL)
            assert mock_store.call_count > 0

    def test_skip_prediction_below_confidence(self, analyzer):
        analyzer._config["tickers"] = ["AAPL"]
        analyzer._config["min_confidence"] = 0.9
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction") as mock_store,
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.resolve_predictions", return_value=0),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            mock_store.assert_not_called()

    def test_sends_whatsapp_alert(self, analyzer):
        analyzer._config["tickers"] = ["AAPL"]
        analyzer._config["alert_whatsapp"] = True
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.resolve_predictions", return_value=0),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
            patch("app.services.whatsapp_service.send_alert") as mock_alert,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            assert mock_alert.call_count >= 1

    def test_handles_ticker_error(self, analyzer):
        analyzer._config["tickers"] = ["AAPL"]

        def raise_error(**kwargs):
            raise ValueError("Network error")

        n_strategies = 6
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=raise_error),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.resolve_predictions", return_value=0),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            assert len(analyzer._results) == n_strategies
            assert analyzer._results[0]["signal"] == "ERROR"

    def test_stops_early_when_event_set(self, analyzer):
        analyzer._config["tickers"] = ["AAPL", "MSFT", "GOOGL"]
        analyzer._stop_event.set()

        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.resolve_predictions", return_value=0),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            # Event set before any future runs, but futures already submitted
            assert len(analyzer._results) == 0

    def test_persistence_to_db(self, analyzer):
        analyzer._config["tickers"] = ["AAPL"]
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.resolve_predictions", return_value=0),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            mock_session.add.assert_called()
            mock_session.commit.assert_called_once()

    def test_resolve_predictions_error_handled(self, analyzer):
        analyzer._config["tickers"] = ["AAPL"]
        n_strategies = 6
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.resolve_predictions", side_effect=Exception("Resolve error")),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            assert len(analyzer._results) == n_strategies

    def test_broadcast_error_handled(self, analyzer):
        analyzer._config["tickers"] = ["AAPL"]
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.resolve_predictions", return_value=0),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            mock_ws.broadcast.side_effect = Exception("Broadcast error")
            analyzer._run_cycle()

    def test_last_run_updated(self, analyzer):
        analyzer._config["tickers"] = ["AAPL"]
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.resolve_predictions", return_value=0),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            assert analyzer._config["last_run"] is not None

    def test_results_capped_at_max_results(self, analyzer):
        analyzer._config["tickers"] = ["AAPL"] * 10
        analyzer._config["max_results"] = 10
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.resolve_predictions", return_value=0),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            assert len(analyzer._results) <= 10

    def test_persistence_db_error_handled(self, analyzer):
        analyzer._config["tickers"] = ["AAPL"]
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.resolve_predictions", return_value=0),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_session.commit.side_effect = Exception("Commit error")
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            assert len(analyzer._results) == 6

    def test_alert_whatsapp_only_for_buy_sell(self, analyzer):
        def fake_neutral(**kwargs):
            return {
                "signal": "NEUTRAL",
                "confidence": 0.5,
                "indicators": {"price": 100.0},
                "reasons": ["Nothing"],
            }

        analyzer._config["tickers"] = ["AAPL"]
        analyzer._config["alert_whatsapp"] = True
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_neutral),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.resolve_predictions", return_value=0),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
            patch("app.services.whatsapp_service.send_alert") as mock_alert,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            mock_alert.assert_not_called()

    def test_alert_whatsapp_disabled(self, analyzer):
        analyzer._config["tickers"] = ["AAPL"]
        analyzer._config["alert_whatsapp"] = False
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.resolve_predictions", return_value=0),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
            patch("app.services.whatsapp_service.send_alert") as mock_alert,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            mock_alert.assert_not_called()


class TestCoverage:
    def test_loop_catches_run_cycle_error(self, analyzer):
        """_loop lines 133-135: exception in _run_cycle is caught."""
        with patch.object(analyzer, "_run_cycle", side_effect=ValueError("boom")):
            t = threading.Thread(target=analyzer._loop, daemon=True)
            t.start()
            time.sleep(0.3)
            analyzer._stop_event.set()
            t.join(timeout=2)

    def test_loop_sleep_exits_via_stop_event(self, analyzer):
        """_loop line 138: sleep loop breaks on stop_event."""
        with patch.object(analyzer, "_run_cycle"):
            t = threading.Thread(target=analyzer._loop, daemon=True)
            t0 = time.monotonic()
            t.start()
            time.sleep(0.3)
            analyzer._stop_event.set()
            t.join(timeout=2)
            assert time.monotonic() - t0 < 3

    def test_whatsapp_import_exception_path(self, analyzer):
        """_run_cycle lines 222-223: send_alert raises -> except: pass."""
        analyzer._config["tickers"] = ["AAPL"]
        analyzer._config["alert_whatsapp"] = True
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
            patch("app.services.whatsapp_service.send_alert", side_effect=ValueError("fail")),
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()

    def test_stop_event_breaks_as_completed(self, analyzer):
        """_run_cycle line 173: as_completed loop breaks on stop_event."""
        analyzer._config["tickers"] = ["AAPL", "MSFT"]

        def slow_run(**kwargs):
            time.sleep(0.5)
            return fake_run_analysis(**kwargs)

        def delayed_stop():
            time.sleep(0.3)
            analyzer._stop_event.set()

        threading.Thread(target=delayed_stop, daemon=True).start()
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=slow_run),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            assert len(analyzer._results) == 0

    def test_future_raises_exception(self, analyzer):
        analyzer._config["tickers"] = ["AAPL"]
        with (
            patch.object(analyzer, "_analyze_single", side_effect=RuntimeError("future boom")),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()
            assert len(analyzer._results) == 0

    def test_resolve_outcomes_raises(self, analyzer):
        analyzer._config["tickers"] = ["AAPL"]
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction"),
            patch("app.services.background_analyzer.resolve_outcomes", side_effect=ValueError("outcome error")),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()

    def test_store_prediction_raises(self, analyzer):
        analyzer._config["tickers"] = ["AAPL"]
        with (
            patch("app.services.background_analyzer.run_analysis", side_effect=fake_run_analysis),
            patch("app.services.background_analyzer.store_prediction", side_effect=ValueError("store error")),
            patch("app.services.background_analyzer.resolve_outcomes"),
            patch("app.services.background_analyzer.store_analysis_result"),
            patch("app.services.background_analyzer.SessionLocal") as mock_sl,
            patch("app.services.ws_manager.ws_manager") as mock_ws,
        ):
            mock_session = MagicMock()
            mock_sl.return_value = mock_session
            mock_ws.broadcast = MagicMock()
            analyzer._run_cycle()

    def test_shutdown(self, analyzer):
        analyzer.shutdown()
