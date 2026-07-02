// ── State ──────────────────────────────────────────────────────
let AUTH = null;
let activityChart = null;

// ── Clock ──────────────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  document.getElementById('clock').textContent = now.toUTCString().replace('GMT', 'UTC');
}
setInterval(updateClock, 1000);
updateClock();

// ── Login ──────────────────────────────────────────────────────
async function doLogin() {
  const user = document.getElementById('login-user').value;
  const pass = document.getElementById('login-pass').value;
  const creds = btoa(`${user}:${pass}`);

  try {
    const res = await fetch('/api/stats', {
      headers: { 'Authorization': `Basic ${creds}` }
    });
    if (res.ok) {
      AUTH = creds;
      document.getElementById('login-overlay').style.display = 'none';
      startDashboard();
    } else {
      document.getElementById('login-error').style.display = 'block';
    }
  } catch {
    document.getElementById('login-error').style.display = 'block';
  }
}

document.getElementById('login-pass').addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});

// ── API helpers ────────────────────────────────────────────────
async function api(path) {
  const res = await fetch(path, { headers: { 'Authorization': `Basic ${AUTH}` } });
  if (!res.ok) throw new Error(res.status);
  return res.json();
}

// ── Activity chart ─────────────────────────────────────────────
function initChart() {
  const ctx = document.getElementById('chart-activity').getContext('2d');
  activityChart = new Chart(ctx, {
    type: 'bar',
    data: { labels: [], datasets: [{
      label: 'requests',
      data: [],
      backgroundColor: 'rgba(88,166,255,0.25)',
      borderColor: '#58a6ff',
      borderWidth: 1,
      borderRadius: 2,
    }]},
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: {
        backgroundColor: '#161b22',
        borderColor: '#21262d',
        borderWidth: 1,
        titleColor: '#6e7681',
        bodyColor: '#c9d1d9',
        bodyFont: { family: 'JetBrains Mono' },
      }},
      scales: {
        x: { grid: { color: '#21262d' }, ticks: { color: '#6e7681', font: { family: 'JetBrains Mono', size: 10 }, maxTicksLimit: 8 }},
        y: { grid: { color: '#21262d' }, ticks: { color: '#6e7681', font: { family: 'JetBrains Mono', size: 10 } }, beginAtZero: true },
      }
    }
  });
}

function updateChart(data) {
  const sorted = [...data].sort((a, b) => a.hour.localeCompare(b.hour));
  activityChart.data.labels   = sorted.map(d => d.hour.slice(11, 16));
  activityChart.data.datasets[0].data = sorted.map(d => d.count);
  activityChart.update('none');
}

// ── Status codes ───────────────────────────────────────────────
function updateStatus(dist) {
  let s2 = 0, s3 = 0, s4 = 0, s5 = 0;
  for (const d of dist) {
    const c = d.status;
    if (c >= 200 && c < 300) s2 += d.count;
    else if (c >= 300 && c < 400) s3 += d.count;
    else if (c >= 400 && c < 500) s4 += d.count;
    else if (c >= 500) s5 += d.count;
  }
  document.getElementById('s2xx').textContent = s2 > 999 ? (s2/1000).toFixed(1)+'k' : s2;
  document.getElementById('s3xx').textContent = s3 > 999 ? (s3/1000).toFixed(1)+'k' : s3;
  document.getElementById('s4xx').textContent = s4 > 999 ? (s4/1000).toFixed(1)+'k' : s4;
  document.getElementById('s5xx').textContent = s5 > 999 ? (s5/1000).toFixed(1)+'k' : s5;
}

// ── Top IPs ────────────────────────────────────────────────────
function updateTopIPs(ips) {
  const container = document.getElementById('top-ips');
  if (!ips.length) { container.innerHTML = '<div class="empty">No data</div>'; return; }
  const max = ips[0].count;
  container.innerHTML = ips.slice(0, 6).map(ip => `
    <div class="ip-row">
      <span class="ip-addr">${ip.ip}</span>
      <div class="ip-bar-wrap"><div class="ip-bar" style="width:${Math.round(ip.count/max*100)}%"></div></div>
      <span class="ip-count">${ip.count}</span>
    </div>
  `).join('');
}

// ── Alerts ─────────────────────────────────────────────────────
function updateAlerts(alerts) {
  const container = document.getElementById('alerts-list');
  document.getElementById('kpi-alerts').textContent = alerts.length;
  if (!alerts.length) { container.innerHTML = '<div class="empty">No alerts</div>'; return; }
  container.innerHTML = alerts.map(a => {
    const time = new Date(a.timestamp).toLocaleTimeString('en-GB');
    return `
      <div class="alert-row ${a.type}">
        <span class="alert-time">${time}</span>
        <span class="alert-type ${a.type}">${a.type.replace('_', ' ')}</span>
        <span class="alert-ip">${a.ip}</span>
        <span class="alert-detail">${a.detail || ''}</span>
      </div>
    `;
  }).join('');
}

// ── World map pings ────────────────────────────────────────────
// Coordonnées approximatives [lon, lat] → [x, y] sur le viewBox 1000x500
// Mapping pays → coordonnée approximative sur la carte SVG simplifiée
const COUNTRY_COORDS = {
  // Europe
  FR: [480, 75], DE: [495, 68], GB: [462, 62], ES: [460, 85],
  IT: [500, 85], NL: [480, 62], BE: [478, 66], CH: [490, 75],
  PL: [510, 62], RU: [600, 55], UA: [530, 70], SE: [505, 45],
  NO: [495, 38], FI: [525, 40], DK: [494, 57],
  // Americas
  US: [160, 120], CA: [140, 80], MX: [150, 175], BR: [210, 320],
  AR: [190, 390], CO: [175, 245], CL: [175, 370],
  // Asia
  CN: [750, 110], JP: [820, 100], KR: [800, 105], IN: [635, 160],
  SG: [735, 200], TH: [720, 175], ID: [750, 210], VN: [730, 170],
  PH: [775, 175], TW: [790, 130], HK: [775, 140],
  // Middle East
  SA: [570, 145], AE: [595, 150], TR: [545, 90], IL: [545, 120],
  // Africa
  ZA: [510, 330], NG: [480, 215], EG: [530, 130], KE: [545, 240],
  MA: [455, 130],
  // Oceania
  AU: [800, 330], NZ: [880, 370],
};

let pingSeq = 0;
const seenIPs = new Set();

function addPing(x, y, color = '#58a6ff') {
  const layer = document.getElementById('pings-layer');
  const id = `ping-${pingSeq++}`;
  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  g.id = id;

  // Point central
  const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  dot.setAttribute('cx', x); dot.setAttribute('cy', y);
  dot.setAttribute('r', 3);
  dot.setAttribute('fill', color);
  g.appendChild(dot);

  // Cercle qui s'étend et s'estompe
  const ring = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  ring.setAttribute('cx', x); ring.setAttribute('cy', y);
  ring.setAttribute('r', 3);
  ring.setAttribute('fill', 'none');
  ring.setAttribute('stroke', color);
  ring.setAttribute('stroke-width', '1.5');
  ring.setAttribute('opacity', '0.8');
  g.appendChild(ring);

  layer.appendChild(g);

  // Animation JS
  const start = performance.now();
  const duration = 2200;

  function frame(now) {
    const t = Math.min((now - start) / duration, 1);
    ring.setAttribute('r', 3 + t * 28);
    ring.setAttribute('opacity', (1 - t) * 0.8);
    dot.setAttribute('opacity', t < 0.6 ? 1 : 1 - (t - 0.6) / 0.4);
    if (t < 1) requestAnimationFrame(frame);
    else g.remove();
  }
  requestAnimationFrame(frame);
}

function triggerPingsFromRequests(requests) {
  for (const req of requests) {
    if (seenIPs.has(req.id)) continue;
    seenIPs.add(req.id);

    // Coordonnées aléatoires dans les zones continentales si pas de géoloc
    // Ici on place sur la carte selon un hash simple de l'IP
    const parts = (req.ip || '0.0.0.0').split('.').map(Number);
    const x = 80  + ((parts[0] * 7 + parts[1] * 3) % 820);
    const y = 30  + ((parts[1] * 5 + parts[2] * 2) % 430);

    // Couleur selon statut HTTP
    const color = req.status >= 400 ? '#f85149'
                : req.status >= 300 ? '#d29922'
                : '#3fb950';

    // Légère dispersion temporelle
    setTimeout(() => addPing(x, y, color), Math.random() * 800);
  }
}

// ── Refresh ────────────────────────────────────────────────────
async function refresh() {
  try {
    const [stats, alerts, recent] = await Promise.all([
      api('/api/stats'),
      api('/api/alerts?limit=30'),
      api('/api/requests/recent?limit=40'),
    ]);

    document.getElementById('kpi-total').textContent =
      stats.total_requests > 9999
        ? (stats.total_requests / 1000).toFixed(1) + 'k'
        : stats.total_requests;

    document.getElementById('kpi-ips').textContent = stats.top_ips.length;

    updateChart(stats.requests_over_time);
    updateStatus(stats.status_distribution);
    updateTopIPs(stats.top_ips);
    updateAlerts(alerts);
    triggerPingsFromRequests(recent);

    document.getElementById('status-dot').style.background = 'var(--green)';
    document.getElementById('status-dot').style.boxShadow  = '0 0 6px var(--green)';
  } catch {
    document.getElementById('status-dot').style.background = 'var(--red)';
    document.getElementById('status-dot').style.boxShadow  = '0 0 6px var(--red)';
  }
}

// ── Start ──────────────────────────────────────────────────────
function startDashboard() {
  initChart();
  refresh();
  setInterval(refresh, 15000); // refresh toutes les 15s
}