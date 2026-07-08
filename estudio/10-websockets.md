# WebSockets — Tiempo Real

> **Fecha:** 2026-07-08

## ¿Qué es un WebSocket?

WebSocket es un **protocolo de comunicación bidireccional** que mantiene
una conexión permanente abierta entre el cliente y el servidor.

### HTTP vs WebSocket

```
HTTP (nuestra app ANTES):
  Cliente → ¿Hay datos? → Servidor → No.
  Cliente → ¿Hay datos? → Servidor → No.
  Cliente → ¿Hay datos? → Servidor → Sí.  ← 99% de los requests son al pedo

WebSocket (nuestra app AHORA):
  Cliente → Conecto y escucho → Servidor → ...
                    push ← Acá tenés los datos
                    push ← Más datos
  El servidor avisa cuando hay novedades. Conexión permanente.
```

## ¿Para qué sirve en nuestra app?

| Antes (polling) | Ahora (WebSocket) |
|-----------------|-------------------|
| Frontend preguntaba cada 5s "¿hay resultados nuevos?" | Server avisa cuando el background analyzer termina un ciclo |
| Consumo innecesario de CPU/red | Sin overhead |
| Latencia de hasta 5s | Latencia de milisegundos |
| El backend tenía que responder aunque no hubiera datos | El backend solo envía cuando hay novedades |

## Cómo lo implementamos

### Servidor (Python/FastAPI)

```python
# app/services/ws_manager.py
class ConnectionManager:
    def __init__(self):
        self._connections: set[WebSocket] = set()

    async def connect(self, ws):   # Acepta conexión
        await ws.accept()
        self._connections.add(ws)

    def disconnect(self, ws):      # Elimina conexión
        self._connections.discard(ws)

    async def broadcast(self, data):  # Envía a TODOS
        for ws in self._connections:
            await ws.send_text(json.dumps(data))

ws_manager = ConnectionManager()  # Singleton
```

### Endpoint WebSocket

```python
# app/main.py
@app.websocket("/api/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()    # Espera mensajes
    except Exception:
        pass
    finally:
        ws_manager.disconnect(ws)
```

### Broadcast desde Background Analyzer

Cuando el background analyzer termina un ciclo, avisa por WebSocket:

```python
# app/services/background_analyzer.py (dentro de _run_cycle)
asyncio.run(ws_manager.broadcast({
    "type": "background_results",
    "data": batch_results,
    "timestamp": "...",
}))
```

Usamos `asyncio.run()` para llamar a una función async desde un thread sync.

### Cliente (JavaScript)

```javascript
// app/static/app.js
const ws = new WebSocket('ws://localhost:8000/api/ws');

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'background_results') {
        actualizarUI(msg.data);  // Los datos llegan solos
    }
};

ws.onclose = () => {
    setTimeout(conectarWebSocket, 5000);  // Reconexión automática
};
```

## ¿Qué datos empuja el WebSocket?

Cuando el background analyzer completa un ciclo, envía:

```json
{
  "type": "background_results",
  "data": [
    {"ticker": "AAPL",  "signal": "NEUTRAL", "confidence": 0.0},
    {"ticker": "TSLA",  "signal": "BUY",     "confidence": 0.75},
    {"ticker": "BTC-USD","signal": "SELL",    "confidence": 0.60}
  ],
  "timestamp": "2026-07-08T20:00:00+00:00"
}
```

## 📚 Para investigar más

| Tema | Por qué | Dónde |
|------|---------|-------|
| **WebSocket protocol** | Cómo funciona a nivel de red (handshake, frames) | RFC 6455 |
| **FastAPI WebSockets** | Más opciones: close codes, subprotocols | https://fastapi.tiangolo.com/advanced/websockets/ |
| **Socket.IO** | Capa sobre WS con fallback (rooms, namespaces) | https://socket.io/ |
| **Server-Sent Events (SSE)** | Alternativa más simple (solo server→client) | https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events |
| **WebSocket seguro (wss://)** | Cifrado TLS como HTTPS | Mismo certificado que el servidor |
| **Reconexión** | Manejo de caídas de red | exponential backoff, max retries |
