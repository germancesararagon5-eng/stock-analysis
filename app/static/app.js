const API = '';

// ════════════════════════════════════════════════════════════════
//  POPULAR TICKERS
// ════════════════════════════════════════════════════════════════
const POPULAR_TICKERS = [
  {sym:'AAPL',name:'Apple Inc.'},{sym:'MSFT',name:'Microsoft Corp.'},
  {sym:'GOOGL',name:'Alphabet Inc.'},{sym:'AMZN',name:'Amazon.com Inc.'},
  {sym:'NVDA',name:'NVIDIA Corp.'},{sym:'META',name:'Meta Platforms Inc.'},
  {sym:'TSLA',name:'Tesla Inc.'},{sym:'BRK.B',name:'Berkshire Hathaway'},
  {sym:'JPM',name:'JPMorgan Chase'},{sym:'V',name:'Visa Inc.'},
  {sym:'JNJ',name:'Johnson & Johnson'},{sym:'WMT',name:'Walmart Inc.'},
  {sym:'PG',name:'Procter & Gamble'},{sym:'MA',name:'Mastercard Inc.'},
  {sym:'UNH',name:'UnitedHealth Group'},{sym:'HD',name:'Home Depot Inc.'},
  {sym:'DIS',name:'Walt Disney Co.'},{sym:'BAC',name:'Bank of America'},
  {sym:'NFLX',name:'Netflix Inc.'},{sym:'ADBE',name:'Adobe Inc.'},
  {sym:'CRM',name:'Salesforce Inc.'},{sym:'PEP',name:'PepsiCo Inc.'},
  {sym:'KO',name:'Coca-Cola Co.'},{sym:'INTC',name:'Intel Corp.'},
  {sym:'AMD',name:'Advanced Micro Devices'},{sym:'CSCO',name:'Cisco Systems'},
  {sym:'CMCSA',name:'Comcast Corp.'},{sym:'TMO',name:'Thermo Fisher Scientific'},
  {sym:'ABBV',name:'AbbVie Inc.'},{sym:'NKE',name:'Nike Inc.'},
  {sym:'MRK',name:'Merck & Co.'},{sym:'AVGO',name:'Broadcom Inc.'},
  {sym:'TXN',name:'Texas Instruments'},{sym:'QCOM',name:'Qualcomm Inc.'},
  {sym:'COST',name:'Costco Wholesale'},{sym:'PYPL',name:'PayPal Holdings'},
  {sym:'UBER',name:'Uber Technologies'},{sym:'SQ',name:'Block Inc.'},
  {sym:'SNAP',name:'Snap Inc.'},{sym:'SPY',name:'SPDR S&P 500 ETF'},
  {sym:'QQQ',name:'Invesco QQQ Trust'},{sym:'DIA',name:'SPDR Dow Jones ETF'},
  {sym:'BTC-USD',name:'Bitcoin USD'},{sym:'ETH-USD',name:'Ethereum USD'},
  {sym:'SOL-USD',name:'Solana USD'},{sym:'BNB-USD',name:'BNB USD'},
  {sym:'XRP-USD',name:'XRP USD'},{sym:'GC=F',name:'Gold Futures'},
  {sym:'CL=F',name:'Crude Oil Futures'},
];

// ════════════════════════════════════════════════════════════════
//  INFO DEFINITIONS
// ════════════════════════════════════════════════════════════════
const INFO = {
  broker: {
    title:'Broker Activo',
    desc:'El broker es la fuente de datos financieros. Yahoo Finance es gratis para datos históricos y en tiempo real. Binance conecta con el exchange de cripto. Interactive Brokers es para trading profesional con acciones y forex.',
    link:'https://www.investopedia.com/terms/b/broker.asp',
    linkLabel:'Investopedia: ¿Qué es un Broker?',
  },
  strategy: {
    title:'Estrategia de Trading',
    desc:'Scalping busca ganancias rápidas en minutos usando EMA, RSI y Bollinger Bands. Swing busca tendencias de días a semanas usando MACD, SMA 200 y niveles de soporte/resistencia.',
    link:'https://www.investopedia.com/terms/s/scalping.asp',
    linkLabel:'Investopedia: Scalping vs Swing Trading',
  },
  interval: {
    title:'Intervalo de Velas',
    desc:'Define el timeframe de cada vela en el gráfico. 1m/5m para scalping, 15m/1h para intradía, 1d para swing. A menor intervalo, más ruido pero señales más tempranas.',
    link:'https://www.investopedia.com/terms/t/timeframe.asp',
    linkLabel:'Investopedia: Timeframes en Trading',
  },
  confidence: {
    title:'Confianza de la Señal',
    desc:'Porcentaje entre 0% y 100% que indica la fuerza de la señal. Se calcula sumando pesos de cada indicador que coincide: EMA crossover (+35%), RSI extremo (+25%), Bollinger/S&R (+20%).',
    link:'https://www.investopedia.com/terms/c/confidencerating.asp',
    linkLabel:'Investopedia: Confidence Rating',
  },
  ema: {
    title:'EMA (Media Móvil Exponencial)',
    desc:'Da más peso a precios recientes. EMA 9 es rápida, EMA 21 es lenta. Cuando la rápida cruza arriba de la lenta es señal de compra (golden cross).',
    link:'https://www.investopedia.com/terms/e/ema.asp',
    linkLabel:'Investopedia: Exponential Moving Average',
  },
  rsi: {
    title:'RSI (Relative Strength Index)',
    desc:'Oscila entre 0 y 100. Mide la velocidad y magnitud de cambios de precio. Sobreventa (<30) sugiere compra, sobrecompra (>70) sugiere venta.',
    link:'https://www.investopedia.com/terms/r/rsi.asp',
    linkLabel:'Investopedia: Relative Strength Index',
  },
  bollinger: {
    title:'Bollinger Bands',
    desc:'Banda superior e inferior a 2 desviaciones estándar de una media móvil de 20 periodos. Cuando el precio toca la banda inferior hay soporte; la superior, resistencia.',
    link:'https://www.investopedia.com/terms/b/bollingerbands.asp',
    linkLabel:'Investopedia: Bollinger Bands',
  },
  macd: {
    title:'MACD (Moving Average Conv. Div.)',
    desc:'Mide la relación entre dos medias móviles. Cuando la línea MACD cruza arriba la línea de señal es momentum alcista. El histograma muestra la fuerza.',
    link:'https://www.investopedia.com/terms/m/macd.asp',
    linkLabel:'Investopedia: MACD Indicator',
  },
  sma200: {
    title:'SMA 200 (Media Simple 200)',
    desc:'Media del precio de cierre de los últimos 200 días. Es el indicador de tendencia a largo plazo más usado. Precio arriba = mercado alcista, abajo = bajista.',
    link:'https://www.investopedia.com/terms/s/sma.asp',
    linkLabel:'Investopedia: Simple Moving Average',
  },
  alerts: {
    title:'Alertas Automáticas',
    desc:'Configura condiciones para recibir notificaciones cuando se cumplan. Pueden enviarse por WhatsApp (Baileys auto-hosteado) cuando se detecte una señal de compra o venta.',
  },
  debug: {
    title:'Depuración y Trazabilidad',
    desc:'Registra cada request, cambio de broker, evaluación de estrategia y error. Útil para auditar señales, medir tiempos de respuesta y diagnosticar fallos.',
    link:'https://fastapi.tiangolo.com/tutorial/middleware/',
    linkLabel:'FastAPI Middleware Docs',
  },
  support_resistance: {
    title:'Soporte y Resistencia',
    desc:'Niveles de precio donde históricamente el activo ha rebotado (soporte) o ha encontrado ventas (resistencia). Se calculan con histograma de densidad de precios.',
    link:'https://www.investopedia.com/terms/s/support.asp',
    linkLabel:'Investopedia: Support & Resistance',
  },
};

// ════════════════════════════════════════════════════════════════
//  UTILITY FUNCTIONS
// ════════════════════════════════════════════════════════════════

/* ── Auth ──────────────────────────────────────── */
function getToken() { return localStorage.getItem('token'); }
function setToken(t) { localStorage.setItem('token', t); }
function clearToken() { localStorage.removeItem('token'); }

async function api(method, path, body) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = 'Bearer ' + token;
  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  if (res.status === 401 && path !== '/api/auth/login') {
    clearToken(); showAuthScreen();
    return null;
  }
  return res.json();
}

function showAuthScreen() {
  document.getElementById('auth-screen').style.display = 'flex';
  document.getElementById('app-header').style.display = 'none';
  document.querySelector('main').style.display = 'none';
}

function showApp() {
  document.getElementById('auth-screen').style.display = 'none';
  document.getElementById('app-header').style.display = 'flex';
  document.querySelector('main').style.display = 'block';
}

function showRegister() {
  document.getElementById('login-form').style.display = 'none';
  document.getElementById('register-form').style.display = 'block';
  document.getElementById('register-error').textContent = '';
}
function showLogin() {
  document.getElementById('register-form').style.display = 'none';
  document.getElementById('login-form').style.display = 'block';
  document.getElementById('login-error').textContent = '';
}

async function handleLogin() {
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;
  const err = document.getElementById('login-error');
  if (!username || !password) { err.textContent = 'Completá todos los campos'; return; }
  err.textContent = '';
  const res = await fetch(API + '/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json();
  if (!res.ok) { err.textContent = data.detail || 'Error al iniciar sesión'; return; }
  setToken(data.access_token);
  showApp();
  document.getElementById('user-display').textContent = username;
  initApp();
}

async function handleRegister() {
  const username = document.getElementById('register-username').value.trim();
  const email = document.getElementById('register-email').value.trim();
  const password = document.getElementById('register-password').value;
  const err = document.getElementById('register-error');
  if (!username || !email || !password) { err.textContent = 'Completá todos los campos'; return; }
  err.textContent = '';
  const res = await fetch(API + '/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  });
  const data = await res.json();
  if (!res.ok) { err.textContent = data.detail || 'Error al registrarse'; return; }
  setToken(data.access_token);
  showApp();
  document.getElementById('user-display').textContent = username;
  initApp();
}

document.getElementById('login-btn').addEventListener('click', handleLogin);
document.getElementById('register-btn').addEventListener('click', handleRegister);
document.getElementById('logout-btn').addEventListener('click', () => {
  clearToken(); showAuthScreen();
});
['login-username','login-password'].forEach(id =>
  document.getElementById(id).addEventListener('keydown', e => { if (e.key === 'Enter') handleLogin(); })
);
['register-username','register-email','register-password'].forEach(id =>
  document.getElementById(id).addEventListener('keydown', e => { if (e.key === 'Enter') handleRegister(); })
);

function showTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  document.querySelector(`nav button[data-tab="${name}"]`).classList.add('active');
  if (name === 'debug') startDebugPoll();
  else stopDebugPoll();
  if (name === 'options') startOptionsPoll();
  else stopOptionsPoll();
}

function addLog(msg, type) {
  const el = document.getElementById('log-container');
  const d = new Date();
  const line = document.createElement('div');
  if (type === 'err') line.style.color = 'var(--red)';
  else if (type === 'ok') line.style.color = 'var(--green)';
  line.textContent = `[${d.toLocaleTimeString()}] ${msg}`;
  el.appendChild(line);
  el.scrollTop = el.scrollHeight;
}

// ── Info Popups ───────────────────────────────────────────
function initInfoPopups() {
  document.querySelectorAll('.info-trigger').forEach(el => {
    el.addEventListener('click', e => {
      e.stopPropagation();
      const popup = el.nextElementSibling;
      const wasOpen = popup.classList.contains('show');
      document.querySelectorAll('.info-popup.show').forEach(p => p.classList.remove('show'));
      if (!wasOpen) popup.classList.add('show');
    });
  });
  document.addEventListener('click', () => {
    document.querySelectorAll('.info-popup.show').forEach(p => p.classList.remove('show'));
  });
}

function renderInfo(key) {
  const info = INFO[key];
  if (!info) return '';
  return `<span class="info-wrap">
    <span class="info-trigger" title="¿Qué es esto?">i</span>
    <div class="info-popup">
      <h3>${info.title}</h3>
      <p>${info.desc}</p>
      <a href="${info.link}" target="_blank" rel="noopener">↗ ${info.linkLabel}</a>
    </div>
  </span>`;
}

// ════════════════════════════════════════════════════════════════
//  AUTOCOMPLETE TICKER
// ════════════════════════════════════════════════════════════════

function createAutocomplete(inputId, dropdownId, onSelect, multi) {
  const input = document.getElementById(inputId);
  const dropdown = document.getElementById(dropdownId);
  const wrap = input.closest('.autocomplete-wrap');
  const clearBtn = wrap ? wrap.querySelector('.clear-btn') : null;
  let highlightedIdx = -1;
  let currentResults = [];

  function filterItems(query) {
    const q = (multi ? query.split(',').pop() : query).toLowerCase().trim();
    if (!q) return POPULAR_TICKERS.slice(0, 30);
    return POPULAR_TICKERS.filter(t =>
      t.sym.toLowerCase().startsWith(q) ||
      t.sym.toLowerCase().includes(q) ||
      t.name.toLowerCase().includes(q)
    ).slice(0, 50);
  }

  function renderDropdown(results) {
    currentResults = results;
    highlightedIdx = -1;
    if (!results.length) {
      dropdown.innerHTML = '<div class="no-results">No se encontraron tickers</div>';
      dropdown.classList.add('show');
      return;
    }
    dropdown.innerHTML = results.map((t, i) =>
      `<div class="item" data-index="${i}">
        <span class="sym">${t.sym}</span>
        <span class="name">${t.name}</span>
      </div>`
    ).join('');
    dropdown.classList.add('show');

    dropdown.querySelectorAll('.item').forEach(el => {
      el.addEventListener('click', () => {
        const idx = parseInt(el.dataset.index);
        selectItem(results[idx]);
      });
      el.addEventListener('mouseenter', () => {
        dropdown.querySelector('.highlighted')?.classList.remove('highlighted');
        el.classList.add('highlighted');
        highlightedIdx = parseInt(el.dataset.index);
      });
    });
  }

  function selectItem(ticker) {
    if (multi) {
      const parts = input.value.split(',').map(s => s.trim()).filter(Boolean);
      if (!parts.includes(ticker.sym)) {
        parts.push(ticker.sym);
        input.value = parts.join(',') + ',';
      }
    } else {
      input.value = ticker.sym;
      document.getElementById('modal-overlay').classList.remove('show');
    }
    dropdown.classList.remove('show');
    if (clearBtn) clearBtn.classList.add('show');
    input.focus();
    input.dispatchEvent(new Event('change'));
    if (onSelect) onSelect(ticker);
  }

  input.addEventListener('input', () => {
    const val = input.value;
    if (clearBtn) clearBtn.classList.toggle('show', val.length > 0);
    const results = filterItems(val);
    renderDropdown(results);
  });

  input.addEventListener('keydown', e => {
    const items = dropdown.querySelectorAll('.item');
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      highlightedIdx = Math.min(highlightedIdx + 1, currentResults.length - 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      highlightedIdx = Math.max(highlightedIdx - 1, -1);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (highlightedIdx >= 0 && currentResults[highlightedIdx]) {
        selectItem(currentResults[highlightedIdx]);
      } else if (currentResults.length === 1) {
        selectItem(currentResults[0]);
      }
      return;
    } else if (e.key === 'Escape') {
      dropdown.classList.remove('show');
      return;
    }
    // highlight
    dropdown.querySelectorAll('.item').forEach((el, i) => {
      el.classList.toggle('highlighted', i === highlightedIdx);
    });
    if (highlightedIdx >= 0) {
      const el = dropdown.querySelector(`.item[data-index="${highlightedIdx}"]`);
      if (el) el.scrollIntoView({ block: 'nearest' });
    }
  });

  input.addEventListener('blur', () => {
    setTimeout(() => dropdown.classList.remove('show'), 200);
  });

  input.addEventListener('focus', () => {
    const results = filterItems(input.value);
    renderDropdown(results);
  });

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      input.value = '';
      clearBtn.classList.remove('show');
      dropdown.classList.remove('show');
      input.focus();
    });
  }

  // Store reference for external access
  input._autocompleteSelect = selectItem;
}

// ════════════════════════════════════════════════════════════════
//  MARKET DATA MODAL
// ════════════════════════════════════════════════════════════════

async function showMarketModal(ticker) {
  const overlay = document.getElementById('modal-overlay');
  const body = document.getElementById('modal-body');
  overlay.classList.add('show');

  body.innerHTML = `<div style="text-align:center;padding:40px;color:var(--muted)">Cargando datos de ${ticker}...</div>`;

  try {
    const [dataResult, analysisResult] = await Promise.all([
      api('GET', `/api/analysis/data/${ticker}`),
      api('POST', '/api/analysis/analyze', { ticker, strategy:'scalping', interval:'1d', periods:30 }).catch(() => null),
    ]);

    const price = dataResult.price;
    const priceStr = price ? `$${price.toFixed(2)}` : '—';
    const indicators = analysisResult?.indicators || {};
    const error = dataResult.error;

    const stats = [
      { label:'Precio', val: priceStr, cls:'' },
      { label:'RSI 14', val: indicators.rsi_14 ?? '—', cls:'' },
      { label:'EMA 9', val: indicators.ema_9 ? `$${indicators.ema_9}` : '—', cls:'' },
      { label:'SMA 200', val: indicators.sma_200 ? `$${indicators.sma_200}` : '—', cls:'' },
      { label:'MACD', val: indicators.macd ?? '—', cls:'' },
      { label:'Bollinger Upper', val: indicators.bb_upper ? `$${indicators.bb_upper}` : '—', cls:'' },
      { label:'Bollinger Lower', val: indicators.bb_lower ? `$${indicators.bb_lower}` : '—', cls:'' },
    ];

    body.innerHTML = `
      <button class="close" onclick="document.getElementById('modal-overlay').classList.remove('show')">&times;</button>
      <h2>${ticker}</h2>
      <div class="subtitle">
        ${error ? `Error: ${error}` : `Análisis Técnico · ${analysisResult?.strategy?.toUpperCase() || ''} · ${analysisResult?.timestamp ? new Date(analysisResult.timestamp).toLocaleString() : ''}`}
      </div>
      ${error ? '' : `
      <div class="grid">
        ${stats.map(s => `
          <div class="stat">
            <div class="val ${s.cls}">${s.val}</div>
            <div class="lbl">${s.label}</div>
          </div>
        `).join('')}
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
        <h3 style="font-size:13px;color:var(--muted);margin:0">Evolución del Precio (diario)</h3>
        <div style="display:flex;gap:6px;align-items:center">
          <label style="font-size:11px;color:var(--muted)">Periodos:</label>
          <select id="modal-chart-periods" style="width:70px;margin:0;padding:3px 6px;font-size:11px">
            ${[15,30,60,100,200].map(p => `<option value="${p}" ${p===60?'selected':''}>${p}</option>`).join('')}
          </select>
        </div>
      </div>
      <div style="height:140px"><canvas id="sparkline"></canvas></div>
      <div id="modal-analysis" style="margin-top:12px"></div>
      `}
    `;

    if (!error) {
      drawSparkline(ticker);
      loadModalAnalysis(ticker);

      const sel = document.getElementById('modal-chart-periods');
      if (sel) {
        sel.onchange = () => { drawSparkline(ticker); loadModalAnalysis(ticker); };
      }
    }
  } catch (e) {
    body.innerHTML = `<button class="close" onclick="document.getElementById('modal-overlay').classList.remove('show')">&times;</button>
      <h2>${ticker}</h2>
      <div class="subtitle" style="color:var(--red)">Error al cargar datos: ${e.message}</div>`;
  }
}

let sparklineChart = null;

async function drawSparkline(ticker) {
  const canvas = document.getElementById('sparkline');
  if (!canvas) return;

  // Destroy previous chart
  if (sparklineChart) { try { sparklineChart.destroy(); } catch(_) {} sparklineChart = null; }

  const periods = parseInt(document.getElementById('modal-chart-periods')?.value) || 60;
  try {
    const data = await api('GET', `/api/analysis/chart/${ticker}?strategy=scalping&interval=1d&periods=${periods}`);
    const series = data.series;
    if (!series || !series.timestamp?.length || !series.close?.filter(v => v != null).length) {
      throw new Error('Sin datos');
    }

    const labels = series.timestamp.map(t => {
      const d = new Date(t);
      return d.toLocaleDateString([], {month:'short', day:'numeric'});
    });

    const close = series.close;
    const lastPrice = close.filter(v => v != null).pop() || 0;
    const firstPrice = close.filter(v => v != null)[0] || 0;
    const isUp = lastPrice >= firstPrice;
    const lineColor = isUp ? '#3fb950' : '#f85149';

    const bbUpper = series.bb_upper || [];
    const bbLower = series.bb_lower || [];

    sparklineChart = new Chart(canvas, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'BB Superior',
            data: bbUpper.map(v => v ?? null),
            borderColor: 'rgba(88,166,255,0.25)',
            borderWidth: 1, pointRadius: 0, fill: false, tension: 0.2,
          },
          {
            label: 'BB Inferior',
            data: bbLower.map(v => v ?? null),
            borderColor: 'rgba(88,166,255,0.25)',
            borderWidth: 1, pointRadius: 0, fill: '-1', tension: 0.2,
          },
          {
            label: 'Cierre',
            data: close,
            borderColor: lineColor,
            backgroundColor: ctx => {
              const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, 140);
              g.addColorStop(0, isUp ? 'rgba(63,185,80,0.2)' : 'rgba(248,81,73,0.2)');
              g.addColorStop(1, 'rgba(0,0,0,0)');
              return g;
            },
            borderWidth: 2, pointRadius: 0, fill: true, tension: 0.2,
          },
          {
            label: 'EMA 9',
            data: series.ema_9 || [],
            borderColor: 'rgba(88,166,255,0.6)',
            borderWidth: 1.5, pointRadius: 0, fill: false, tension: 0.2,
          },
          {
            label: 'EMA 21',
            data: series.ema_21 || [],
            borderColor: 'rgba(209,154,102,0.6)',
            borderWidth: 1.5, pointRadius: 0, fill: false, tension: 0.2,
          },
        ].filter(d => d.data.some(v => v != null)),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#1c2333',
            titleColor: '#c9d1d9',
            bodyColor: '#c9d1d9',
            borderColor: '#58a6ff',
            borderWidth: 1,
            padding: 8,
            bodyFont: { size: 11 },
            callbacks: {
              label: ctx => { if (ctx.parsed.y == null) return null; return ctx.dataset.label + ': $' + ctx.parsed.y.toFixed(2); },
            },
          },
          zoom: {
            pan: { enabled: true, mode: 'x' },
            zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' },
          },
        },
        scales: {
          x: { display: true, ticks: { color: '#8b949e', maxTicksLimit: 8, font: { size: 9 } }, grid: { color: 'rgba(48,54,61,0.4)' } },
          y: { position: 'right', ticks: { color: '#8b949e', font: { size: 9 }, callback: v => '$' + v.toFixed(0) }, grid: { color: 'rgba(48,54,61,0.2)' } },
        },
        elements: { point: { radius: 0 } },
      },
    });
  } catch (e) {
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#8b949e';
    ctx.font = '16px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Datos insuficientes', canvas.width/2, canvas.height/2);
  }
}

async function loadModalAnalysis(ticker) {
  const container = document.getElementById('modal-analysis');
  if (!container) return;
  try {
    container.innerHTML = '<div style="text-align:center;padding:12px;color:var(--muted);font-size:12px">Analizando...</div>';
    const r = await api('POST', '/api/analysis/technical-analysis?ticker=' + encodeURIComponent(ticker) + '&strategy=scalping&interval=1d&periods=' + (parseInt(document.getElementById('modal-chart-periods')?.value) || 60));
    renderTechnicalAnalysis(container, r);
  } catch (_) {
    container.innerHTML = '';
  }
}

function renderTechnicalAnalysis(container, r) {
  const v = r.verdict || 'NEUTRAL';
  const conf = r.confidence || 0;
  const isBullish = v === 'BUY' || v === 'ACCUMULATE';
  const color = isBullish ? 'var(--green)' : (v === 'SELL' || v === 'REDUCE' ? 'var(--red)' : 'var(--muted)');
  const signalIcons = {
    'bullish': '📈', 'bearish': '📉', 'overbought': '⚠️', 'oversold': '💡', 'neutral': '➖',
  };
  container.innerHTML = `
    <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:var(--bg);border-radius:8px;border-left:3px solid ${color}">
      <div style="text-align:center;min-width:80px">
        <div style="font-size:18px;font-weight:700;color:${color}">${v}</div>
        <div style="font-size:10px;color:var(--muted)">${conf}% confianza</div>
      </div>
      <div style="flex:1;font-size:11px;color:var(--muted)">
        <div style="display:flex;gap:6px;margin-bottom:4px;flex-wrap:wrap">
          ${(r.signals || []).map(s => `<span style="font-size:10px;background:var(--card);padding:1px 6px;border-radius:4px">${signalIcons[s]||''} ${s}</span>`).join('')}
        </div>
        <div>${(r.reasons || []).slice(0, 3).join(' · ')}</div>
      </div>
      <button class="btn sm" onclick="loadFullAnalysis('${r.ticker}')" title="Análisis completo">🔍</button>
    </div>
  `;
}

async function loadFullAnalysis(ticker) {
  const periods = parseInt(document.getElementById('modal-chart-periods')?.value) || 60;
  try {
    const r = await api('POST', '/api/analysis/technical-analysis?ticker=' + encodeURIComponent(ticker) + '&strategy=scalping&interval=1d&periods=' + periods);
    const container = document.getElementById('modal-analysis');
    const v = r.verdict || 'NEUTRAL';
    const conf = r.confidence || 0;
    const isBullish = v === 'BUY' || v === 'ACCUMULATE';
    const color = isBullish ? 'var(--green)' : (v === 'SELL' || v === 'REDUCE' ? 'var(--red)' : 'var(--muted)');
    container.innerHTML = `
      <div style="background:var(--bg);border-radius:8px;padding:14px;border-left:3px solid ${color}">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
          <div>
            <strong style="font-size:14px;color:${color}">${v}</strong>
            <span style="font-size:11px;color:var(--muted)"> · ${conf}% confianza</span>
          </div>
          <button class="btn sm" onclick="document.getElementById('modal-analysis').innerHTML=''">✕</button>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:6px;margin-bottom:10px">
          ${Object.entries(r.indicators || {}).filter(([,val]) => val != null).map(([k, val]) => `
            <div style="background:var(--card);border-radius:4px;padding:4px 8px;font-size:11px">
              <div style="color:var(--muted)">${k.replace(/_/g,' ').toUpperCase()}</div>
              <div style="font-weight:600">${typeof val === 'number' ? (k.includes('bb') || k.includes('macd') ? val.toFixed(2) : val.toFixed(1)) : val}</div>
            </div>
          `).join('')}
        </div>
        <div style="font-size:11px;color:var(--muted)">
          <strong>Señales:</strong> ${(r.signals || []).join(', ') || 'neutral'}<br>
          <strong>Razonamiento:</strong>
          <ul style="margin:4px 0 0 16px;padding:0">
            ${(r.reasons || []).map(rev => `<li style="margin-bottom:2px">${rev}</li>`).join('')}
          </ul>
        </div>
      </div>
    `;
  } catch (_) {}
}

// ════════════════════════════════════════════════════════════════
//  DASHBOARD
// ════════════════════════════════════════════════════════════════

async function loadDashboard() {
  const health = await api('GET', '/health');
  document.getElementById('dash-broker').textContent = health.active_broker || 'Ninguno';
  const dot = document.getElementById('dash-dot');
  dot.className = 'status-dot ' + (health.broker_connected ? 'online' : 'offline');
  document.getElementById('dash-status').textContent = health.broker_connected ? 'Conectado' : 'Desconectado';
}

// ════════════════════════════════════════════════════════════════
//  ANALYSIS
// ════════════════════════════════════════════════════════════════

async function runAnalysis() {
  const ticker = document.getElementById('an-ticker').value.trim().toUpperCase();
  const strategy = document.getElementById('an-strategy').value;
  const interval = document.getElementById('an-interval').value;
  const periods = parseInt(document.getElementById('an-periods').value) || 100;
  if (!ticker) return;

  const btn = document.getElementById('an-btn');
  btn.disabled = true; btn.textContent = 'Analizando...';
  const result = await api('POST', '/api/analysis/analyze', { ticker, strategy, interval, periods });
  btn.disabled = false; btn.textContent = 'Analizar';
  showAnalysisResult(result);
}

// ── Dashboard data button ───────────────────────────────────
async function getData() {
  const ticker = document.getElementById('dash-data-ticker').value.trim().toUpperCase();
  if (!ticker) return;
  const data = await api('GET', '/api/analysis/data/' + ticker);
  document.getElementById('data-result').textContent = JSON.stringify(data, null, 2);
  if (!data.error) {
    showMarketModal(ticker);
  } else {
    addLog('[DATA] Error ' + ticker + ': ' + data.error, 'err');
  }
}

function fmt(v) { return v ?? '—'; }

function indicatorColor(cls, val, low, high) {
  if (cls === 'rsi') {
    if (val < 30) return { color: 'var(--green)', label: 'Sobreventa (BUY)' };
    if (val > 70) return { color: 'var(--red)', label: 'Sobrecompra (SELL)' };
    return { color: 'var(--muted)', label: 'Neutral' };
  }
  if (cls === 'ema_cross') {
    if (val > 0) return { color: 'var(--green)', label: 'EMA 9 > EMA 21 (alcista)' };
    if (val < 0) return { color: 'var(--red)', label: 'EMA 9 < EMA 21 (bajista)' };
    return { color: 'var(--muted)', label: 'EMA 9 = EMA 21 (plano)' };
  }
  if (cls === 'bb') {
    if (val < 0) return { color: 'var(--green)', label: 'Precio bajo banda (soporte)' };
    if (val > 0) return { color: 'var(--red)', label: 'Precio sobre banda (resistencia)' };
    return { color: 'var(--muted)', label: 'Precio en banda media' };
  }
  if (cls === 'macd') {
    if (val > 0) return { color: 'var(--green)', label: 'Momentum alcista' };
    if (val < 0) return { color: 'var(--red)', label: 'Momentum bajista' };
    return { color: 'var(--muted)', label: 'Neutral' };
  }
  if (cls === 'sma') {
    if (val > 0) return { color: 'var(--green)', label: 'Sobre SMA 200 (alcista LP)' };
    if (val < 0) return { color: 'var(--red)', label: 'Bajo SMA 200 (bajista LP)' };
    return { color: 'var(--muted)', label: 'En SMA 200' };
  }
  return { color: 'var(--text)', label: '' };
}

function showAnalysisResult(r) {
  const container = document.getElementById('an-result');
  container.style.display = 'block';

  const price = r.indicators?.price;
  const ema9 = r.indicators?.ema_9;
  const ema21 = r.indicators?.ema_21;
  const rsi = r.indicators?.rsi_14;
  const bbUpper = r.indicators?.bb_upper;
  const bbLower = r.indicators?.bb_lower;
  const macd = r.indicators?.macd;
  const sma200 = r.indicators?.sma_200;

  const emaCross = (ema9 && ema21) ? ema9 - ema21 : null;
  const bbPos = (price && bbUpper && bbLower)
    ? (price > bbUpper ? 1 : price < bbLower ? -1 : 0) : null;
  const smaPos = (price && sma200) ? price - sma200 : null;

  const ec = indicatorColor('ema_cross', emaCross);
  const rc = indicatorColor('rsi', rsi);
  const bc = indicatorColor('bb', bbPos);
  const mc = indicatorColor('macd', macd);
  const sc = indicatorColor('sma', smaPos);

  const reasonsHtml = r.reasons?.length
    ? r.reasons.map(rs => `<li style="color:var(--muted);font-size:13px">${rs}</li>`).join('')
    : '<li style="color:var(--muted)">Sin señales activas</li>';

  const ticker = r.ticker;
  const strategy = r.strategy || 'scalping';
  const interval = r.interval || '5m';

  container.innerHTML = `
    <div class="card fade-in">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
        <h2 style="margin:0;text-transform:none;font-size:20px;display:flex;align-items:center;gap:8px">
          ${ticker}
          <button class="btn outline sm" onclick="showMarketModal('${ticker}')" title="Ver datos de mercado">📊 Mercado</button>
        </h2>
        <span style="margin-left:auto;font-size:13px;color:var(--muted)">
          ${r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : ''}
        </span>
      </div>

      <div class="row" style="align-items:center;margin-bottom:16px">
        <div>
          <span class="badge ${r.signal === 'BUY' ? 'buy' : r.signal === 'SELL' ? 'sell' : 'neutral'}" style="font-size:18px;padding:6px 20px">
            ${r.signal}
          </span>
          <span style="margin-left:12px;font-size:14px;color:var(--muted)">
            Confianza: ${(r.confidence * 100).toFixed(0)}%
            ${renderInfo('confidence')}
          </span>
        </div>
        <div style="margin-left:auto;font-size:13px;color:var(--muted)">
          ${(strategy).toUpperCase()} · ${interval}
          ${renderInfo('strategy')}
        </div>
      </div>

      <div class="indicators">
        <div class="indicator" style="border-left:3px solid ${rc.color}">
          <div class="value" style="color:${rc.color}">${fmt(rsi)}</div>
          <div class="label">RSI 14 ${renderInfo('rsi')}</div>
          <div style="font-size:10px;color:${rc.color};margin-top:4px">${rc.label}</div>
        </div>
        <div class="indicator" style="border-left:3px solid ${ec.color}">
          <div class="value" style="color:${ec.color}">${fmt(ema9)} / ${fmt(ema21)}</div>
          <div class="label">EMA 9 / 21 ${renderInfo('ema')}</div>
          <div style="font-size:10px;color:${ec.color};margin-top:4px">${ec.label}</div>
        </div>
        <div class="indicator" style="border-left:3px solid ${bc.color}">
          <div class="value" style="color:${bc.color}">${fmt(bbLower)} – ${fmt(bbUpper)}</div>
          <div class="label">Bollinger ${renderInfo('bollinger')}</div>
          <div style="font-size:10px;color:${bc.color};margin-top:4px">${bc.label}</div>
        </div>
        <div class="indicator">
          <div class="value" style="font-size:24px">$${fmt(price)}</div>
          <div class="label">Precio Actual</div>
        </div>
        ${strategy === 'swing' ? `
        <div class="indicator" style="border-left:3px solid ${mc.color}">
          <div class="value" style="color:${mc.color}">${fmt(macd)}</div>
          <div class="label">MACD ${renderInfo('macd')}</div>
          <div style="font-size:10px;color:${mc.color};margin-top:4px">${mc.label}</div>
        </div>
        <div class="indicator" style="border-left:3px solid ${sc.color}">
          <div class="value" style="color:${sc.color}">${fmt(sma200)}</div>
          <div class="label">SMA 200 ${renderInfo('sma200')}</div>
          <div style="font-size:10px;color:${sc.color};margin-top:4px">${sc.label}</div>
        </div>
        <div class="indicator">
          <div class="value">${fmt(r.indicators?.nearest_support)}</div>
          <div class="label">Soporte ${renderInfo('support_resistance')}</div>
        </div>
        <div class="indicator">
          <div class="value">${fmt(r.indicators?.nearest_resistance)}</div>
          <div class="label">Resistencia ${renderInfo('support_resistance')}</div>
        </div>
        ` : ''}
      </div>

      <div style="margin-top:16px">
        <strong style="font-size:13px">Razones:</strong>
        <ul style="margin:8px 0 0 16px">${reasonsHtml}</ul>
      </div>

      <div class="chart-section" style="margin-top:20px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
          <strong style="font-size:13px">Gráfico de Precio e Indicadores</strong>
          <div style="display:flex;gap:8px;align-items:center">
            <label style="font-size:11px;color:var(--muted);display:flex;align-items:center;gap:4px">
              Periodos:
              <select id="chart-periods" style="width:80px;margin:0;padding:4px 8px;font-size:12px">
                ${[30,60,100,200,300,500].map(p => `<option value="${p}" ${p===100?'selected':''}>${p}</option>`).join('')}
              </select>
            </label>
            <button class="btn outline sm" id="chart-refresh-btn" style="padding:4px 10px;font-size:12px;margin:0">⟳</button>
          </div>
        </div>
        <div id="chart-panels" style="position:relative;margin-top:8px">
          <div id="chart-loading" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:13px;background:var(--bg);border-radius:6px;z-index:10">Cargando gráfico…</div>
        </div>
        <div id="chart-analysis" style="margin-top:8px"></div>
      </div>
    </div>
  `;
  initInfoPopups();

  // Period selector listener
  const sel = document.getElementById('chart-periods');
  const btn = document.getElementById('chart-refresh-btn');
  if (sel) {
    sel.onchange = () => fetchChart(ticker, strategy, interval, parseInt(sel.value));
  }
  if (btn) {
    btn.onclick = () => fetchChart(ticker, strategy, interval, parseInt(sel?.value || 100));
  }

  // Fetch chart data and draw
  fetchChart(ticker, strategy, interval, parseInt(sel?.value || 100));

  // Show AI assistant card
  const aiCard = document.getElementById('ai-assistant-card');
  if (aiCard) aiCard.style.display = 'block';
}

// ── Chart.js multi-panel chart ─────────────────────────────
let chartInstances = [];

function destroyCharts() {
  chartInstances.forEach(c => { try { c.destroy(); } catch(_) {} });
  chartInstances = [];
}

const CHART_COLORS = {
  txt: '#8b949e',
  grid: 'rgba(48,54,61,0.4)',
  price: '#c9d1d9',
  ema9: '#58a6ff',
  ema21: '#d29922',
  bb: 'rgba(88,166,255,0.25)',
  green: 'rgba(63,185,80,0.5)',
  red: 'rgba(248,81,73,0.5)',
  rsiFill: 'rgba(201,217,217,0.06)',
};

const CHART_TOOLTIP = {
  backgroundColor: '#1c2333',
  titleColor: '#c9d1d9',
  bodyColor: '#c9d1d9',
  borderColor: '#58a6ff',
  borderWidth: 1,
  padding: 8,
  bodyFont: { size: 11 },
};

const CHART_SCALES_X = {
  display: true,
  ticks: { color: '#8b949e', maxTicksLimit: 8, font: { size: 9 } },
  grid: { color: 'rgba(48,54,61,0.4)' },
};

function addPanel(container, id, height) {
  const wrap = document.createElement('div');
  wrap.style.cssText = `height:${height}px;margin-top:4px;background:var(--bg);border-radius:6px;position:relative`;
  wrap.innerHTML = `<canvas id="${id}"></canvas>`;
  container.appendChild(wrap);
  return document.getElementById(id);
}

async function fetchChart(ticker, strategy, interval, periods) {
  try {
    const [data, analysis] = await Promise.all([
      api('GET', `/api/analysis/chart/${ticker}?strategy=${strategy}&interval=${interval}&periods=${periods}`),
      api('POST', `/api/analysis/technical-analysis?ticker=${encodeURIComponent(ticker)}&strategy=${strategy}&interval=${interval}&periods=${periods}`).catch(() => null),
    ]);
    document.getElementById('chart-loading').style.display = 'none';
    drawChart(data.series, strategy);
    const analysisContainer = document.getElementById('chart-analysis');
    if (analysisContainer && analysis) {
      renderTechnicalAnalysis(analysisContainer, analysis);
    }
  } catch (e) {
    document.getElementById('chart-loading').textContent = 'Error al cargar gráfico: ' + e.message;
  }
}

function drawChart(series, strategy) {
  const pan = document.getElementById('chart-panels');
  if (!pan || !series || !series.timestamp?.length) return;

  destroyCharts();
  // Remove old panels (keep loading overlay)
  Array.from(pan.children).forEach(c => {
    if (c.id !== 'chart-loading') c.remove();
  });

  const labels = series.timestamp.map(t => {
    const d = new Date(t);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
  });

  const { txt, grid, price: pCol, ema9, ema21, bb } = CHART_COLORS;

  // ── Panel 1: Price + EMAs + BB ──
    const canvas1 = addPanel(pan, 'chart-panel-price', 200);
  const bbUpper = series.bb_upper?.map(v => v ?? null) || [];
  const bbLower = series.bb_lower?.map(v => v ?? null) || [];

  const panel1 = new Chart(canvas1, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'BB Superior',
          data: bbUpper,
          borderColor: bb, backgroundColor: bb,
          borderWidth: 1, pointRadius: 0, fill: false, tension: 0.2,
        },
        {
          label: 'BB Inferior',
          data: bbLower,
          borderColor: bb, backgroundColor: bb,
          borderWidth: 1, pointRadius: 0, fill: '-1', tension: 0.2,
        },
        {
          label: 'Precio',
          data: series.close || [],
          borderColor: pCol, borderWidth: 2, pointRadius: 0, fill: false, tension: 0.2,
        },
        {
          label: 'EMA 9',
          data: series.ema_9 || [],
          borderColor: ema9, borderWidth: 1.5, pointRadius: 0, fill: false, tension: 0.2,
        },
        {
          label: 'EMA 21',
          data: series.ema_21 || [],
          borderColor: ema21, borderWidth: 1.5, pointRadius: 0, fill: false, tension: 0.2,
        },
      ].filter(d => d.data.some(v => v != null)),
    },
      options: {
        responsive: true, maintainAspectRatio: false,
        animation: { duration: 300 },
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { position: 'top', labels: { color: txt, boxWidth: 12, padding: 6, font: { size: 10 } } },
          tooltip: { ...CHART_TOOLTIP, callbacks: { label: ctx => ctx.parsed.y != null ? ctx.dataset.label + ': $' + ctx.parsed.y.toFixed(2) : null } },
          zoom: { pan: { enabled: true, mode: 'x' }, zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' } },
        },
        scales: {
          x: CHART_SCALES_X,
          y: { position: 'right', ticks: { color: txt, font: { size: 9 }, callback: v => '$' + v.toFixed(0) }, grid: { color: grid } },
        },
      },
  });
  chartInstances.push(panel1);

  // ── Panel 2: RSI ──
    const canvas2 = addPanel(pan, 'chart-panel-rsi', 90);
  const rsiData = series.rsi_14 || [];

  const panel2 = new Chart(canvas2, {
    type: 'line',
    data: {
      labels: labels.slice(labels.length - rsiData.length),
      datasets: [
        {
          label: 'Sobrecompra (70)',
          data: rsiData.map(() => 70),
          borderColor: 'rgba(248,81,73,0.2)', borderWidth: 1, borderDash: [4, 4], pointRadius: 0, fill: false,
        },
        {
          label: 'Sobreventa (30)',
          data: rsiData.map(() => 30),
          borderColor: 'rgba(63,185,80,0.2)', borderWidth: 1, borderDash: [4, 4], pointRadius: 0, fill: false,
        },
        {
          label: 'RSI 14',
          data: rsiData,
          borderColor: pCol,
          backgroundColor: ctx => {
            const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, 90);
            g.addColorStop(0, 'rgba(248,81,73,0.08)');
            g.addColorStop(0.3, 'rgba(201,217,217,0.02)');
            g.addColorStop(0.7, 'rgba(201,217,217,0.02)');
            g.addColorStop(1, 'rgba(63,185,80,0.08)');
            return g;
          },
          borderWidth: 2, pointRadius: 0, fill: true, tension: 0.3,
        },
      ],
    },
      options: {
        responsive: true, maintainAspectRatio: false,
        animation: { duration: 300 },
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { position: 'top', labels: { color: txt, boxWidth: 10, padding: 4, font: { size: 9 } } },
          tooltip: {
            ...CHART_TOOLTIP,
            callbacks: {
              label: ctx => {
                const v = ctx.parsed.y;
                if (v == null) return null;
                let extra = '';
                if (v > 70) extra = ' ⚠️ Sobrecompra';
                else if (v < 30) extra = ' 💡 Sobreventa';
                return ctx.dataset.label + ': ' + v.toFixed(1) + extra;
              },
            },
          },
          zoom: { pan: { enabled: true, mode: 'x' }, zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' } },
        },
        scales: {
          x: { ...CHART_SCALES_X, ticks: { ...CHART_SCALES_X.ticks, maxTicksLimit: 6 } },
          y: {
            min: 0, max: 100, position: 'right',
            ticks: { color: txt, font: { size: 9 } },
            grid: {
              color: ctx => {
                const v = ctx.tick.value;
                if (v === 30) return 'rgba(63,185,80,0.15)';
                if (v === 70) return 'rgba(248,81,73,0.15)';
                if (v === 50) return 'rgba(139,148,158,0.15)';
                return grid;
              },
            },
          },
        },
      },
  });
  chartInstances.push(panel2);

  // ── Panel 3: MACD (solo swing) ──
  if (strategy === 'swing' && series.macd?.some(v => v != null)) {
    const canvas3 = addPanel(pan, 'chart-panel-macd', 80);
    const macdData = series.macd || [];
    const signalData = series.macd_signal || [];
    const histData = series.macd_histogram || [];
    const histColors = histData.map(v => v >= 0 ? 'rgba(63,185,80,0.5)' : 'rgba(248,81,73,0.5)');
    const macdLabels = labels.slice(labels.length - macdData.length);

    const panel3 = new Chart(canvas3, {
      type: 'bar',
      data: {
        labels: macdLabels,
        datasets: [
          {
            label: 'MACD', data: macdData,
            type: 'line', borderColor: ema9, borderWidth: 1.5, pointRadius: 0, fill: false, tension: 0.2,
            order: 1,
          },
          {
            label: 'Señal', data: signalData,
            type: 'line', borderColor: ema21, borderWidth: 1.5, pointRadius: 0, fill: false, tension: 0.2,
            order: 1,
          },
          {
            label: 'Histograma', data: histData,
            backgroundColor: histColors, borderColor: histColors, borderWidth: 1, barPercentage: 0.6,
            order: 2,
          },
        ],
      },
        options: {
          responsive: true, maintainAspectRatio: false,
          animation: { duration: 300 },
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { position: 'top', labels: { color: txt, boxWidth: 10, padding: 4, font: { size: 9 } } },
            tooltip: { ...CHART_TOOLTIP, callbacks: { label: ctx => ctx.parsed.y != null ? ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(2) : null } },
            zoom: { pan: { enabled: true, mode: 'x' }, zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' } },
          },
          scales: {
            x: { ...CHART_SCALES_X, ticks: { ...CHART_SCALES_X.ticks, maxTicksLimit: 6 } },
            y: { position: 'right', ticks: { color: txt, font: { size: 9 } }, grid: { color: grid } },
          },
        },
    });
    chartInstances.push(panel3);
  }
}

// ════════════════════════════════════════════════════════════════
//  ORDER
// ════════════════════════════════════════════════════════════════

async function placeOrder() {
  const ticker = document.getElementById('ord-ticker').value.trim().toUpperCase();
  const side = document.getElementById('ord-side').value;
  const qty = parseFloat(document.getElementById('ord-qty').value);
  if (!ticker || !qty) return;
  const result = await api('POST', '/api/analysis/order', { ticker, side, quantity: qty });
  addLog('[ORDER] ' + result.ticker + ' ' + result.side + ' ' + result.quantity + ': ' + result.status, result.error ? 'err' : 'ok');
}

// ════════════════════════════════════════════════════════════════
//  ALERTS
// ════════════════════════════════════════════════════════════════

async function loadAlerts() {
  const alerts = await api('GET', '/api/alerts/');
  const tbody = document.getElementById('alerts-tbody');
  if (!alerts.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty">Sin alertas configuradas</td></tr>';
    return;
  }
  tbody.innerHTML = alerts.map(a => `
    <tr>
      <td><strong>${a.ticker}</strong></td>
      <td>${a.strategy}</td>
      <td>${a.condition} ${a.threshold ?? ''}</td>
      <td><span class="badge ${a.whatsapp_enabled ? 'buy' : 'neutral'}">${a.whatsapp_enabled ? 'WhatsApp' : 'Solo log'}</span></td>
      <td><button class="btn red sm" onclick="deleteAlert(${a.id})">Eliminar</button></td>
    </tr>
  `).join('');
}

async function createAlert() {
  const ticker = document.getElementById('al-ticker').value.trim().toUpperCase();
  const payload = {
    ticker,
    strategy: document.getElementById('al-strategy').value,
    condition: document.getElementById('al-condition').value,
    threshold: parseFloat(document.getElementById('al-threshold').value) || null,
    whatsapp_enabled: document.getElementById('al-whatsapp').checked,
  };
  if (!ticker) return;
  await api('POST', '/api/alerts/', payload);
  document.getElementById('al-ticker').value = '';
  loadAlerts();
  addLog('[ALERT] Creada: ' + ticker + ' ' + payload.condition, 'ok');
}

async function deleteAlert(id) {
  await api('DELETE', '/api/alerts/' + id);
  loadAlerts();
}

async function testWhatsApp() {
  const result = await api('POST', '/api/alerts/test-whatsapp');
  addLog('[WHATSAPP] ' + result.status, result.status === 'sent' ? 'ok' : 'err');
}

// ════════════════════════════════════════════════════════════════
//  DEBUG
// ════════════════════════════════════════════════════════════════

let debugPollId = 0;

async function loadDebug() {
  const data = await api('GET', '/api/debug/');
  document.getElementById('debug-enabled').textContent = data.enabled ? 'Activado' : 'Desactivado';
  document.getElementById('debug-stats').innerHTML = `
    <div class="indicator"><div class="value">${data.stats.total_requests}</div><div class="label">Requests</div></div>
    <div class="indicator"><div class="value">${data.stats.total_errors}</div><div class="label">Errores</div></div>
    <div class="indicator"><div class="value">${data.stats.broker_switches}</div><div class="label">Cambios broker</div></div>
    <div class="indicator"><div class="value">${data.stats.strategy_runs}</div><div class="label">Análisis</div></div>
  `;
  document.getElementById('debug-broker').textContent = data.active_broker || 'Ninguno';
  const st = document.getElementById('debug-broker-status');
  st.textContent = data.broker_connected ? 'Conectado' : 'Desconectado';
  st.style.color = data.broker_connected ? 'var(--green)' : 'var(--red)';
  document.getElementById('debug-events').textContent = JSON.stringify(data.recent_broker_events || [], null, 2);
  document.getElementById('debug-errors').textContent = JSON.stringify(data.recent_errors || [], null, 2);
  document.getElementById('debug-requests').textContent = JSON.stringify(data.recent_requests || [], null, 2);
  document.getElementById('debug-strategy').textContent = JSON.stringify(data.recent_strategy_evals || [], null, 2);
  applyDebugFilter();
}

function applyDebugFilter() {
  const filter = document.getElementById('debug-filter').value;
  document.querySelectorAll('.debug-panel').forEach(p => {
    p.style.display = (filter === 'all' || p.id === 'debug-panel-' + filter) ? '' : 'none';
  });
}

async function toggleDebug() {
  const r = await api('POST', '/api/debug/toggle');
  document.getElementById('debug-enabled').textContent = r.enabled ? 'Activado' : 'Desactivado';
}

async function clearDebug() {
  await api('POST', '/api/debug/clear');
  loadDebug();
}

function startDebugPoll() {
  if (debugPollId) return;
  debugPollId = setInterval(() => loadDebug(), 3000);
}
function stopDebugPoll() {
  clearInterval(debugPollId);
  debugPollId = 0;
}

// ════════════════════════════════════════════════════════════════
//  OPTIONS TAB (BACKGROUND ANALYZER + BROKER + DEBUG CONFIG)
// ════════════════════════════════════════════════════════════════

let optionsPollId = 0;

async function loadOptions() {
  // ── Broker status ──
  try {
    const health = await api('GET', '/health');
    const brokers = await api('GET', '/api/config/brokers');
    const sel = document.getElementById('opt-broker-select');
    sel.innerHTML = brokers.available_brokers.map(b =>
      `<option value="${b}" ${b === health.active_broker ? 'selected' : ''}>${b}</option>`
    ).join('');
    document.getElementById('opt-broker-status').textContent =
      health.broker_connected ? 'Conectado' : 'Desconectado';
  } catch (_) {}

  // ── Debug status ──
  try {
    const ds = await api('GET', '/api/options/debug/status');
    document.getElementById('opt-debug-toggle').checked = ds.enabled;
    document.getElementById('opt-debug-label').textContent = ds.enabled ? 'Activado' : 'Desactivado';
    document.getElementById('opt-debug-label').style.color = ds.enabled ? 'var(--green)' : 'var(--muted)';
  } catch (_) {}

  // ── WhatsApp status ──
  await loadWhatsAppConfig();

  // ── Background status ──
  await loadBackgroundStatus();
  await loadBackgroundResults();

  // ── Prediction stats ──
  const predTicker = document.getElementById('pred-filter').value.trim().toUpperCase();
  await loadPredictionStats(predTicker);
  await loadPredictions(predTicker);
}

async function toggleBackgroundAnalyzer() {
  const currentlyOn = document.getElementById('bg-toggle').checked;
  if (currentlyOn) {
    await api('POST', '/api/options/background/start');
    addLog('[BG] Analizador iniciado', 'ok');
  } else {
    await api('POST', '/api/options/background/stop');
    addLog('[BG] Analizador detenido', 'err');
  }
  // Revertir visualmente si la API falla
  const s = await loadBackgroundStatus();
  if (s && s.enabled !== currentlyOn) {
    document.getElementById('bg-toggle').checked = s.enabled;
  }
}

async function loadBackgroundStatus() {
  try {
    const s = await api('GET', '/api/options/background/status');
    document.getElementById('bg-toggle').checked = s.enabled;
    document.getElementById('bg-status-label').textContent = s.enabled ? 'Activo' : 'Detenido';
    document.getElementById('bg-status-label').style.color = s.enabled ? 'var(--green)' : 'var(--muted)';
    document.getElementById('bg-last-run').textContent = 'Última ejecución: ' + (s.last_run ? new Date(s.last_run).toLocaleString() : '—');
    document.getElementById('bg-tickers').value = (s.tickers || []).join(',');
    document.getElementById('bg-strategy').value = s.strategy || 'scalping';
    document.getElementById('bg-interval').value = s.interval || '5m';
    document.getElementById('bg-periods').value = s.periods || 100;
    document.getElementById('bg-min-conf').value = s.min_confidence || 0.2;
    document.getElementById('bg-every').value = s.run_every_seconds || 300;
    document.getElementById('bg-whatsapp').checked = s.alert_whatsapp || false;
    return s;
  } catch (_) { return null; }
}

async function configureBackgroundAnalyzer() {
  const tickers = document.getElementById('bg-tickers').value.trim();
  const strategy = document.getElementById('bg-strategy').value;
  const interval = document.getElementById('bg-interval').value;
  const periods = parseInt(document.getElementById('bg-periods').value) || 100;
  const minConf = parseFloat(document.getElementById('bg-min-conf').value) || 0.2;
  const every = parseInt(document.getElementById('bg-every').value) || 300;
  const whatsapp = document.getElementById('bg-whatsapp').checked;

  await api('POST', '/api/options/background/config'
    + '?tickers=' + encodeURIComponent(tickers)
    + '&strategy=' + strategy
    + '&interval=' + interval
    + '&periods=' + periods
    + '&min_confidence=' + minConf
    + '&alert_whatsapp=' + whatsapp
    + '&run_every_seconds=' + every
  );
  addLog('[BG] Configuración aplicada', 'ok');
  await loadBackgroundStatus();
}

async function loadBackgroundResults() {
  try {
    const r = await api('GET', '/api/options/background/results?limit=20');
    const card = document.getElementById('bg-results-card');
    const pre = document.getElementById('bg-results');
    if (!r.results || !r.results.length) {
      card.style.display = 'none';
      return;
    }
    card.style.display = 'block';
    document.getElementById('bg-results-count').textContent = r.results.length;
    pre.textContent = JSON.stringify(r.results, null, 2);
  } catch (_) {}
}

async function optSwitchBroker() {
  const name = document.getElementById('opt-broker-select').value;
  const sandbox = document.getElementById('opt-sandbox').checked;
  const result = await api('POST', '/api/config/broker', { name, sandbox });
  loadOptions();
  loadDashboard();
  addLog('[CONFIG] Broker: ' + result.broker + ' | ' + result.message, result.connected ? 'ok' : 'err');
}

async function loadWhatsAppConfig() {
  try {
    const c = await api('GET', '/api/options/whatsapp/config');
    document.getElementById('wa-phone').value = c.phone_number || '';
    const qrContainer = document.getElementById('wa-qr-container');
    const connectedInfo = document.getElementById('wa-connected-info');
    const disconnectedInfo = document.getElementById('wa-disconnected-info');
    const statusEl = document.getElementById('wa-status');

    if (c.connected) {
      qrContainer.style.display = 'none';
      connectedInfo.style.display = 'block';
      disconnectedInfo.style.display = 'none';
      document.getElementById('wa-connected-phone').textContent = c.phone || c.phone_number || '—';
      statusEl.textContent = '✅ Conectado';
      statusEl.style.color = 'var(--green)';
    } else {
      connectedInfo.style.display = 'none';
      disconnectedInfo.style.display = 'block';
      statusEl.textContent = c.phone_number ? '⚠️ Número guardado, esperando conexión' : 'No configurado';
      statusEl.style.color = 'var(--muted)';
      // Try to fetch QR
      loadQRCode();
    }
  } catch (_) {}
}

async function loadQRCode() {
  const qrContainer = document.getElementById('wa-qr-container');
  const qrImg = document.getElementById('wa-qr-img');
  try {
    const qr = await api('GET', '/api/options/whatsapp/qr');
    if (qr.qr) {
      qrContainer.style.display = 'block';
      qrImg.src = qr.qr;
    } else {
      qrContainer.style.display = 'none';
    }
  } catch (_) {
    qrContainer.style.display = 'none';
  }
}

async function saveWhatsAppConfig() {
  const phone = document.getElementById('wa-phone').value.trim();
  try {
    const r = await api('POST', '/api/options/whatsapp/config?phone_number=' + encodeURIComponent(phone));
    if (r.status === 'ok') {
      addLog('[WA] Número WhatsApp guardado', 'ok');
      await loadWhatsAppConfig();
    } else {
      addLog('[WA] Error: ' + (r.detail || 'desconocido'), 'err');
    }
  } catch (e) {
    addLog('[WA] Error al guardar: ' + e.message, 'err');
  }
}

async function optToggleDebug() {
  const r = await api('POST', '/api/options/debug/toggle');
  document.getElementById('opt-debug-toggle').checked = r.enabled;
  document.getElementById('opt-debug-label').textContent = r.enabled ? 'Activado' : 'Desactivado';
  document.getElementById('opt-debug-label').style.color = r.enabled ? 'var(--green)' : 'var(--muted)';
  addLog('[DEBUG] ' + (r.enabled ? 'Activado' : 'Desactivado'), 'ok');
}

async function loadPredictionStats(ticker) {
  try {
    let url = '/api/options/predictions/stats';
    if (ticker) url += '?ticker=' + encodeURIComponent(ticker);
    const s = await api('GET', url);
    document.getElementById('pred-total').textContent = s.total || 0;
    document.getElementById('pred-resolved').textContent = s.resolved || 0;
    document.getElementById('pred-correct').textContent = s.correct || 0;
    document.getElementById('pred-pending').textContent = s.pending || 0;
    document.getElementById('pred-accuracy').textContent = (s.accuracy_pct || 0) + '%';
    return s;
  } catch (_) { return null; }
}

async function loadPredictions(ticker) {
  try {
    let url = '/api/options/predictions?limit=30';
    if (ticker) url += '&ticker=' + encodeURIComponent(ticker);
    const r = await api('GET', url);
    const tbody = document.getElementById('pred-tbody');
    const card = document.getElementById('pred-list-card');
    if (!r.predictions || !r.predictions.length) {
      card.style.display = 'none';
      return;
    }
    card.style.display = 'block';
    tbody.innerHTML = r.predictions.map(p => {
      const outcomeLabel = p.outcome === 'CORRECT' ? '✅' : p.outcome === 'INCORRECT' ? '❌' : '⏳';
      const outcomeCls = p.outcome === 'CORRECT' ? 'buy' : p.outcome === 'INCORRECT' ? 'sell' : 'neutral';
      const chgCls = p.price_change_pct > 0 ? 'pos' : p.price_change_pct < 0 ? 'neg' : '';
      return `<tr>
        <td><strong>${p.ticker}</strong></td>
        <td><span class="badge ${p.signal === 'BUY' ? 'buy' : 'sell'}">${p.signal}</span></td>
        <td>${(p.confidence * 100).toFixed(0)}%</td>
        <td>${p.price_at_prediction ? '$' + p.price_at_prediction.toFixed(2) : '—'}</td>
        <td><span class="badge ${outcomeCls}">${outcomeLabel} ${p.outcome}</span></td>
        <td class="${chgCls}">${p.price_change_pct != null ? (p.price_change_pct > 0 ? '+' : '') + p.price_change_pct + '%' : '—'}</td>
        <td style="font-size:11px;color:var(--muted)">${p.created_at ? new Date(p.created_at).toLocaleString() : '—'}</td>
      </tr>`;
    }).join('');
  } catch (_) {}
}

async function resolvePendingPredictions() {
  const r = await api('POST', '/api/options/predictions/resolve?count=20');
  addLog('[PRED] Resueltas: ' + (r.resolved || 0), r.resolved > 0 ? 'ok' : 'err');
  const ticker = document.getElementById('pred-filter').value.trim().toUpperCase();
  loadPredictionStats(ticker);
  loadPredictions(ticker);
}

function startOptionsPoll() {
  if (optionsPollId) return;
  optionsPollId = setInterval(() => {
    loadBackgroundStatus();
    loadBackgroundResults();
    const ticker = document.getElementById('pred-filter').value.trim().toUpperCase();
    loadPredictionStats(ticker);
  }, 5000);
}
function stopOptionsPoll() {
  clearInterval(optionsPollId);
  optionsPollId = 0;
}

// ════════════════════════════════════════════════════════════════
//  INIT
// ════════════════════════════════════════════════════════════════

function initApp() {
  showTab('dashboard');
  loadDashboard();
  if (window._debugInterval) return;

  document.querySelectorAll('nav button').forEach(b => {
    b.addEventListener('click', () => showTab(b.dataset.tab));
  });

  createAutocomplete('dash-data-ticker', 'dash-data-dropdown');
  createAutocomplete('an-ticker', 'an-dropdown', (t) => {
    document.getElementById('an-btn').click();
  });
  createAutocomplete('ord-ticker', 'ord-dropdown');
  createAutocomplete('al-ticker', 'al-dropdown');
  createAutocomplete('bg-tickers', 'bg-dropdown', null, true);

  document.getElementById('dash-data-btn').addEventListener('click', getData);
  document.getElementById('an-btn').addEventListener('click', runAnalysis);
  document.getElementById('ord-btn').addEventListener('click', placeOrder);

  // ── Alerts ──
  loadAlerts();
  document.getElementById('al-btn').addEventListener('click', createAlert);
  document.getElementById('al-test-wa').addEventListener('click', testWhatsApp);

  // ── Debug ──
  loadDebug();
  document.getElementById('debug-refresh').addEventListener('click', loadDebug);
  document.getElementById('debug-clear').addEventListener('click', clearDebug);
  document.getElementById('debug-filter').addEventListener('change', applyDebugFilter);

  // ── Options ──
  loadOptions();
  document.getElementById('bg-toggle').addEventListener('change', toggleBackgroundAnalyzer);
  document.getElementById('bg-apply-btn').addEventListener('click', configureBackgroundAnalyzer);
  document.getElementById('opt-switch-btn').addEventListener('click', optSwitchBroker);
  document.getElementById('opt-debug-toggle').addEventListener('change', optToggleDebug);
  document.getElementById('wa-save-btn').addEventListener('click', saveWhatsAppConfig);
  document.getElementById('wa-refresh-qr-btn').addEventListener('click', loadQRCode);

  // ── Predictions ──
  document.getElementById('pred-filter-btn').addEventListener('click', () => {
    const ticker = document.getElementById('pred-filter').value.trim().toUpperCase();
    loadPredictionStats(ticker);
    loadPredictions(ticker);
  });
  document.getElementById('pred-resolve-btn').addEventListener('click', resolvePendingPredictions);

  // ── Modal close on overlay click ──
  document.getElementById('modal-overlay').addEventListener('click', e => {
    if (e.target === e.currentTarget) e.target.classList.remove('show');
  });

  // ── Info popups ──
  initInfoPopups();
});

// Check auth on load
const token = getToken();
if (token) {
  fetch(API + '/api/auth/me', { headers: { 'Authorization': 'Bearer ' + token } })
    .then(res => {
      if (res.ok) {
        showApp();
        return res.json();
      }
      throw new Error('invalid');
    })
    .then(user => {
      document.getElementById('user-display').textContent = user.username;
      initApp();
    })
    .catch(() => { clearToken(); showAuthScreen(); });
} else {
  showAuthScreen();
}
