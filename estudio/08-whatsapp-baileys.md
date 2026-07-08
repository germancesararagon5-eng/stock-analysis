# WhatsApp Gateway con Baileys

> **Fecha:** 2026-07-08

## ¿Qué es?

Es un **servicio auto-hosteado** que permite enviar y recibir mensajes
de WhatsApp sin pagar Twilio ni ninguna API externa.

Usa una librería llamada **Baileys** que implementa el protocolo de
WhatsApp Web. Básicamente, emula lo que hace el navegador cuando
escaneás el código QR con tu celular.

## Arquitectura

```
┌─ FastAPI (Python) ─┐         ┌─ Node.js (Baileys) ─┐
│                     │  HTTP   │                       │
│ whatsapp_service.py ├─────────┤ index.js              │
│   → send_alert()    │         │   GET /qr             │
│   → get_qr()        │         │   POST /send-message  │
│   → check_connect() │         │   GET /status         │
└─────────────────────┘         └───────────────────────┘
                                        │
                                   WhatsApp Web (tu celu)
```

## ¿Por qué no Twilio?

| Aspecto | Twilio | Baileys (nuestro) |
|---------|--------|-------------------|
| Costo | Por mensaje (~$0.05) | 0 (gratis) |
| Configuración | API key, Webhooks | Escanear QR |
| Dependencia | Terceros | Auto-hosteado |
| Límites | Los de Twilio | Los de WhatsApp |

## Cómo funciona (para el usuario)

```
1. Ir a Opciones → WhatsApp
2. Click en "Obtener QR"
3. WhatsApp → 3 puntitos → Dispositivos vinculados → Vincular
4. Escanear el QR con el celu
5. ¡Listo! Las alertas te llegan al WhatsApp
```

## El Gateway (Node.js)

```javascript
// whatsapp-gateway/index.js
const { default: makeWASocket, useMultiFileAuthState } = require('baileys');

async function start() {
    const { state, saveCreds } = await useMultiFileAuthState('session');
    const sock = makeWASocket({ auth: state });

    // Express HTTP server
    app.get('/qr', (req, res) => {
        if (lastQR) res.json({ qr: lastQR });
        else res.status(404).json({ error: 'No QR available' });
    });

    app.post('/send-message', (req, res) => {
        await sock.sendMessage(req.body.to + '@s.whatsapp.net', {
            text: req.body.message
        });
    });
}
```

## Persistencia de Sesión

La sesión de WhatsApp se guarda en un **volumen Docker**:

```yaml
volumes:
  - whatsapp-session:/app/session   # No se pierde al reiniciar
```

Si escaneaste el QR una vez, no hace falta escanearlo de nuevo
a menos que cierres sesión desde el celular.

## 📚 Para investigar más

| Tema | Por qué | Dónde |
|------|---------|-------|
| **Baileys GitHub** | Código fuente y issues | https://github.com/WhiskeySockets/Baileys |
| **WhatsApp Web protocol** | Cómo funciona internamente | https://github.com/WhiskeySockets/Baileys/wiki |
| **Express.js** | Framework HTTP de Node.js | https://expressjs.com/ |
| **Node.js 20** | Novedades: permission model, built-in test runner | https://nodejs.org/en/blog/release/v20.0.0 |
| **Alternativas** | whatsapp-web.js, venom-bot | Buscar "whatsapp api nodejs" |
