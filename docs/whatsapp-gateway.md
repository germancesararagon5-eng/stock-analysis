# WhatsApp Gateway

Gateway auto-hosteado para enviar alertas vía WhatsApp usando la librería **Baileys** (emulación del protocolo WhatsApp Web).

## Stack

| Componente | Tecnología |
|------------|-----------|
| Runtime | Node.js 22+ |
| WhatsApp protocol | `@whiskeysockets/baileys` ^6.7.10 |
| HTTP server | Express ^4.21.0 |
| QR generation | `qrcode` ^1.5.4 |
| Logger | Pino + pino-pretty |
| Auth persistence | `useMultiFileAuthState` en `./session/` |

## Arquitectura

```
                    ┌──────────────────┐
                    │   WhatsApp Cloud  │
                    │   (servidores WA) │
                    └────────┬─────────┘
                             │ WebSocket (WA Web)
                             │
┌──────────────┐    ┌───────┴──────────┐    ┌──────────────────┐
│   FastAPI    │    │  WhatsApp Gateway │    │   Teléfono       │
│  :8000       │◄──►│  Node.js :3000    │◄───│   (escanea QR)   │
│              │    │                   │    │                  │
│ POST /analyze│    │ GET /qr (base64)  │    └──────────────────┘
│ GET /qr      │    │ POST /send-message│
│ POST /alert  │    │ GET /status       │
└──────────────┘    └──────────────────┘
```

La app FastAPI se comunica con el gateway vía HTTP (no directamente con WhatsApp).

## Endpoints del Gateway

### `GET /status`
```
Response: { "connected": true/false, "phone": "5492214599962" | null }
```

### `GET /qr`
Retorna el código QR como imagen base64 para escanear con WhatsApp Web.
```
Response: { "qr": "data:image/png;base64,..." }
```
Si no hay QR disponible (ya conectado o gateway iniciando): `404 { "error": "No QR available" }`

### `POST /send-message`
```
Body: { "to": "5492214599962", "message": "Señal BUY para AAPL (conf: 0.80)" }
Response: { "success": true } | { "success": false, "error": "..." }
```

## Ciclo de vida de la conexión

```
1. Gateway inicia → Baileys busca auth en ./session/
2. ¿Hay sesión guardada?
   ├── No  → Genera QR → WAIT (espera escaneo)
   │         Expuesto en GET /qr como base64
   │         Usuario escanea con WhatsApp → CONNECTED
   └── Sí  → Intenta reconectar
              ├── OK → CONNECTED (estado guardado)
              └── Expired → Genera QR nuevo → WAIT
3. CONNECTED: puede enviar mensajes
4. Disconnect:
   ├── Logout → session eliminada → volver a paso 2
   └── Otro   → reconexión automática (start())
```

## Cómo conectarlo

### Opción 1: Docker (producción)
```bash
docker compose up -d whatsapp-gateway
# El QR se expone en GET /api/options/whatsapp/qr (proxy desde FastAPI)
# Abrir http://localhost:8000 → pestaña Opciones → WhatsApp
```

### Opción 2: Manual (desarrollo)
```bash
cd whatsapp-gateway
node index.js
# Gateway en http://localhost:3000
# QR: curl http://localhost:3000/qr | python3 -c "import sys,json; print(json.load(sys.stdin).get('qr',''))"
```

### Opción 3: Local con Node.js (sin Docker)
```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
# En otra terminal:
node whatsapp-gateway/index.js
# Asegurar .env: WHATSAPP_GATEWAY_URL=http://localhost:3000
```

## Persistencia de sesión

La sesión se guarda en `whatsapp-gateway/session/` (o `/app/session/` en Docker).
- `creds.json` — credenciales de autenticación
- `app-state-sync-key-*.json` — estado de sincronización

Si se borra este directorio, hay que escanear el QR de nuevo.
En Docker, usar volumen: `whatsapp-session:/app/session` (docker-compose.yml).

## Troubleshooting

**El QR no aparece:**
- Gateway no está corriendo → verificar `ps aux | grep "node index"`
- Ya hay sesión activa → `GET /status` muestra `connected: true`
- Error de autenticación → borrar `whatsapp-gateway/session/` y reiniciar

**No se envían mensajes:**
- Gateway no conectado → escanear QR de nuevo
- Número destino no configurado → `POST /api/options/whatsapp/config?phone_number=5492214599962`
- Gateway en puerto incorrecto → verificar `WHATSAPP_GATEWAY_URL` en `.env`

**El QR expira rápido:**
Baileys genera QRs con expiración por defecto (~20 segundos). El frontend debe refrescar periódicamente.

## Servicio desde FastAPI

Archivo: `app/services/whatsapp_service.py`

| Función | Descripción |
|---------|-------------|
| `check_connection()` | GET /status del gateway |
| `get_qr()` | GET /qr → base64 o error |
| `send_alert(message, to)` | POST /send-message |
| `update_phone_number(phone)` | Guarda número en DB (whatsapp_configs) |
| `get_config()` | Estado + número guardado |

Las funciones del servicio se llaman desde:
- `options_router.py`: GET/POST `/api/options/whatsapp/*`
- `analysis_service.py`: `send_alert()` si `notify=True` y señal BUY/SELL
- `alerts_router.py`: test WhatsApp
- `background_analyzer.py`: alertas automáticas en cada ciclo
