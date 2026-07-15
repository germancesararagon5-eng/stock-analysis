import { makeWASocket, useMultiFileAuthState, fetchLatestBaileysVersion, DisconnectReason } from '@whiskeysockets/baileys';
import express from 'express';
import qrcode from 'qrcode';
import pino from 'pino';
import { mkdirSync, existsSync, appendFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SESSION_DIR = './session';
const LOG_FILE = join(__dirname, 'gateway.log');
const PORT = parseInt(process.env.PORT || '3001');

function log(level, msg, data = null) {
  const ts = new Date().toISOString();
  const line = `[${ts}] [${level}] ${msg}${data ? ' ' + JSON.stringify(data) : ''}\n`;
  try { appendFileSync(LOG_FILE, line); } catch (_) {}
  if (level === 'ERROR') console.error(line.trim());
  else console.log(line.trim());
}

const pinoLogger = pino({ level: 'warn' });

if (!existsSync(SESSION_DIR)) mkdirSync(SESSION_DIR, { recursive: true });

let sock = null;
let lastQr = null;
let connected = false;
let phoneNumber = null;
let reconnectAttempts = 0;

async function start() {
  let state, version;
  try {
    const r = await useMultiFileAuthState(SESSION_DIR);
    state = r.state;
    saveCreds = r.saveCreds;
    const v = await fetchLatestBaileysVersion();
    version = v.version;
    log('INFO', 'Baileys version', { version });
  } catch (e) {
    log('ERROR', 'Fallo init Baileys', { error: e.message, stack: e.stack?.slice(0, 200) });
    setTimeout(start, 10000);
    return;
  }

  try {
    sock = makeWASocket({
      version,
      logger: pinoLogger,
      printQRInTerminal: false,
      auth: state,
      browser: ['StockAnalysis Bot', 'Chrome', '1.0.0'],
      markOnlineOnConnect: false,
      connectTimeoutMs: 30000,
      keepAliveIntervalMs: 25000,
      syncFullHistory: false,
      generateHighQualityLinkPreview: false,
    });
  } catch (e) {
    log('ERROR', 'Fallo makeWASocket', { error: e.message, stack: e.stack?.slice(0, 200) });
    setTimeout(start, 15000);
    return;
  }

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      lastQr = qr;
      connected = false;
      phoneNumber = null;
      reconnectAttempts = 0;
      log('INFO', 'QR generado');
    }

    if (connection === 'open') {
      connected = true;
      phoneNumber = sock.user?.id?.split(':')[0] || null;
      lastQr = null;
      reconnectAttempts = 0;
      log('INFO', 'WhatsApp conectado', { phone: phoneNumber });
    }

    if (connection === 'close') {
      connected = false;
      const statusCode = lastDisconnect?.error?.output?.statusCode;
      const reason = lastDisconnect?.error?.message || 'unknown';
      log('WARN', 'Conexion cerrada', { statusCode, reason, phone: phoneNumber });
      phoneNumber = null;
      lastQr = null;

      if (statusCode === DisconnectReason.loggedOut) {
        log('ERROR', 'Sesion expirada/logout — borrar session/ para reconectar');
        return;
      }

      reconnectAttempts++;
      const delay = Math.min(reconnectAttempts * 5000, 60000);
      log('INFO', 'Reconectando', { attempt: reconnectAttempts, delay_ms: delay });
      setTimeout(start, delay);
    }

    if (connection === 'error') {
      const errMsg = lastDisconnect?.error?.message || 'unknown error';
      log('ERROR', 'Error de conexion', { error: errMsg, phone: phoneNumber });
      reconnectAttempts++;
      const delay = Math.min(reconnectAttempts * 5000, 60000);
      setTimeout(() => {
        log('INFO', 'Reintentando conexion', { attempt: reconnectAttempts });
        start();
      }, delay);
    }
  });

  if (saveCreds) {
    sock.ev.on('creds.update', saveCreds);
  }
}

let saveCreds = null;

const app = express();
app.use(express.json());

app.get('/status', (_req, res) => {
  res.json({ connected, phone: phoneNumber });
});

app.get('/qr', async (_req, res) => {
  if (!lastQr) return res.status(404).send('<html><body><h2>No QR disponible</h2><p>Esperando a que Baileys genere un nuevo QR...</p></body></html>');
  try {
    const base64 = await qrcode.toDataURL(lastQr, { scale: 6, margin: 1 });
    res.send(`<!DOCTYPE html><html><head><meta charset="utf-8"><title>WhatsApp QR</title><style>body{background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;margin:0;font-family:sans-serif}h2{color:#333;margin-bottom:8px}p{color:#666;font-size:14px;margin-bottom:24px}img{border:8px solid #fff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.15)}</style></head><body><h2>Escanea con WhatsApp</h2><p>Abre WhatsApp > ⋮ > Dispositivos vinculados > Vincular un dispositivo</p><img src="${base64}" alt="QR Code"/></body></html>`);
  } catch (e) {
    res.status(500).send(`<html><body><h2>Error</h2><p>${e.message}</p></body></html>`);
  }
});

app.post('/send-message', (req, res) => {
  const { to, message } = req.body;
  if (!to || !message) return res.status(400).json({ error: 'Missing to or message' });
  if (!connected || !sock) {
    log('WARN', 'Intento de envio sin conexion', { to });
    return res.status(503).json({ error: 'WhatsApp not connected' });
  }

  const jid = to.includes('@s.whatsapp.net') ? to : to.replace(/[^0-9]/g, '') + '@s.whatsapp.net';
  log('INFO', 'Enviando mensaje', { to: jid });
  sock.sendMessage(jid, { text: message })
    .then(() => {
      log('INFO', 'Mensaje enviado OK', { to: jid });
      res.json({ success: true });
    })
    .catch(err => {
      log('ERROR', 'Error al enviar mensaje', { error: err.message, to: jid });
      res.status(500).json({ success: false, error: err.message });
    });
});

app.get('/logs', (_req, res) => {
  try {
    const logs = require('fs').readFileSync(LOG_FILE, 'utf-8');
    const lines = logs.split('\n').filter(Boolean).slice(-200);
    res.json({ logs: lines });
  } catch (e) {
    res.json({ logs: [], error: e.message });
  }
});

app.post('/logs/clear', (_req, res) => {
  try {
    require('fs').writeFileSync(LOG_FILE, '');
    res.json({ status: 'ok' });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

start().then(() => {
  app.listen(PORT, () => {
    log('INFO', 'WhatsApp Gateway iniciado', { port: PORT });
  });
});
