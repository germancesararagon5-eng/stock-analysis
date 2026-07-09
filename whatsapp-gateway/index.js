import { makeWASocket, useMultiFileAuthState, fetchLatestBaileysVersion, DisconnectReason } from '@whiskeysockets/baileys';
import express from 'express';
import qrcode from 'qrcode';
import pino from 'pino';
import { mkdirSync, existsSync } from 'fs';

const SESSION_DIR = './session';
const PORT = parseInt(process.env.PORT || '3001');
const logger = pino({ level: 'info', transport: { target: 'pino-pretty' } });

if (!existsSync(SESSION_DIR)) mkdirSync(SESSION_DIR, { recursive: true });

let sock = null;
let lastQr = null;
let connected = false;
let phoneNumber = null;

async function start() {
  const { state, saveCreds } = await useMultiFileAuthState(SESSION_DIR);
  const { version } = await fetchLatestBaileysVersion();

  sock = makeWASocket({
    version,
    logger,
    printQRInTerminal: false,
    auth: state,
    browser: ['StockAnalysis Bot', 'Chrome', '1.0.0'],
  });

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;
    if (qr) {
      lastQr = qr;
      connected = false;
      phoneNumber = null;
      logger.info('Nuevo QR generado');
    }
    if (connection === 'open') {
      connected = true;
      phoneNumber = sock.user?.id?.split(':')[0] || null;
      lastQr = null;
      logger.info('WhatsApp conectado: %s', phoneNumber);
    }
    if (connection === 'close') {
      connected = false;
      const reason = lastDisconnect?.error?.output?.statusCode;
      const shouldReconnect = reason !== DisconnectReason.loggedOut;
      logger.info('Desconectado, reconectar=%s', shouldReconnect);
      if (shouldReconnect) start();
    }
  });

  sock.ev.on('creds.update', saveCreds);
}

const app = express();
app.use(express.json());

app.get('/status', (_req, res) => {
  res.json({ connected, phone: phoneNumber });
});

app.get('/qr', async (_req, res) => {
  if (!lastQr) return res.status(404).json({ error: 'No QR available' });
  try {
    const base64 = await qrcode.toDataURL(lastQr, { scale: 6, margin: 1 });
    res.json({ qr: base64 });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/send-message', (req, res) => {
  const { to, message } = req.body;
  if (!to || !message) return res.status(400).json({ error: 'Missing to or message' });
  if (!connected || !sock) return res.status(503).json({ error: 'WhatsApp not connected' });

  const jid = to.includes('@s.whatsapp.net') ? to : to.replace(/[^0-9]/g, '') + '@s.whatsapp.net';
  sock.sendMessage(jid, { text: message })
    .then(() => res.json({ success: true }))
    .catch(err => res.status(500).json({ success: false, error: err.message }));
});

start().then(() => {
  app.listen(PORT, () => logger.info('WhatsApp Gateway en puerto %d', PORT));
});
