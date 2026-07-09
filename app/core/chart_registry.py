from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChartDef:
    name: str
    description: str
    endpoint: str
    method: str = "GET"
    params: dict = field(default_factory=dict)
    source: str = ""
    ui_location: str = ""
    requires_data: bool = True


_registry: list[ChartDef] = []


def register_chart(defn: ChartDef) -> None:
    _registry.append(defn)


def get_registered_charts() -> list[ChartDef]:
    return list(_registry)


def unregister_chart(name: str) -> None:
    global _registry
    _registry = [c for c in _registry if c.name != name]


# ── Register all system charts ──────────────────────────────────

register_chart(ChartDef(
    name="sparkline",
    description="Sparkline de precio diario en modal de mercado",
    endpoint="/api/analysis/chart/{ticker}",
    params={"strategy": "scalping", "interval": "1d", "periods": 60},
    source="app.routers.analysis_router.get_chart",
    ui_location="Dashboard → Ver Mercado → gráfico diario",
))

register_chart(ChartDef(
    name="multi-panel",
    description="Gráfico multi-panel en pestaña Análisis (precio + RSI + MACD)",
    endpoint="/api/analysis/chart/{ticker}",
    params={"strategy": "scalping", "interval": "1d", "periods": 100},
    source="app.routers.analysis_router.get_chart",
    ui_location="Pestaña Análisis → panel charts con toggles",
))

register_chart(ChartDef(
    name="technical-analysis",
    description="Análisis técnico detallado con veredicto por indicador",
    endpoint="/api/analysis/technical-analysis",
    method="POST",
    params={"ticker": "{ticker}", "strategy": "scalping", "interval": "1d", "periods": 100},
    source="app.routers.analysis_router.technical_analysis",
    ui_location="Pestaña Análisis → panel de análisis técnico",
))
