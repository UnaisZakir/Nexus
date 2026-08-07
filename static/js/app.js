/**
 * Nexus ERP — Core JavaScript
 * Dynamic UI, Modals, Toast Notifications, AI Chat Widget, Filters
 */

// ── Live Date/Time ───────────────────────────────────
function updateClock() {
  const el = document.getElementById('live-date');
  if (el) {
    const now = new Date();
    el.textContent = now.toLocaleDateString('en-US', {
      weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
    });
  }
}
updateClock();
setInterval(updateClock, 60000);

// ── Toast Notifications ──────────────────────────────
function toast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span style="font-size:1.1rem;">${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
  container.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateX(110%)'; el.style.transition = '0.3s ease'; setTimeout(() => el.remove(), 300); }, duration);
}

// ── Modal System ─────────────────────────────────────
function openModal(id) {
  const overlay = document.getElementById(id);
  if (overlay) overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal(id) {
  const overlay = document.getElementById(id);
  if (overlay) overlay.classList.remove('open');
  document.body.style.overflow = '';
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
    document.body.style.overflow = '';
  }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => {
      m.classList.remove('open');
      document.body.style.overflow = '';
    });
    if (aiPanel) aiPanel.classList.remove('open');
  }
});

// ── Table Search Filter ──────────────────────────────
function filterTable(inputId, tbodyId) {
  const query = document.getElementById(inputId).value.toLowerCase();
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  tbody.querySelectorAll('tr').forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
  });
}

// ── Floating AI Chat Widget ───────────────────────────
const aiPanel  = document.getElementById('ai-panel');
const aiBtn    = document.getElementById('ai-fab-btn');
const aiInput  = document.getElementById('ai-input');
const aiMsgs   = document.getElementById('ai-messages');
const aiSend   = document.getElementById('ai-send-btn');

if (aiBtn && aiPanel) {
  aiBtn.addEventListener('click', () => aiPanel.classList.toggle('open'));
}

async function sendFloatingAI() {
  if (!aiInput || !aiMsgs) return;
  const msg = aiInput.value.trim();
  if (!msg) return;
  aiInput.value = '';

  // User bubble
  const userDiv = document.createElement('div');
  userDiv.className = 'ai-msg user';
  userDiv.textContent = msg;
  aiMsgs.appendChild(userDiv);

  // Typing indicator
  const typing = document.createElement('div');
  typing.className = 'ai-msg ai typing';
  typing.textContent = '● Thinking...';
  aiMsgs.appendChild(typing);
  aiMsgs.scrollTop = aiMsgs.scrollHeight;

  try {
    const r = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ message: msg })
    });
    const d = await r.json();
    typing.remove();
    const aiDiv = document.createElement('div');
    aiDiv.className = 'ai-msg ai';
    aiDiv.style.whiteSpace = 'pre-line';
    aiDiv.textContent = d.reply;
    aiMsgs.appendChild(aiDiv);
    aiMsgs.scrollTop = aiMsgs.scrollHeight;
  } catch {
    typing.textContent = '⚠ Network error. Please try again.';
  }
}

if (aiSend) aiSend.addEventListener('click', sendFloatingAI);
if (aiInput) {
  aiInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); sendFloatingAI(); }
  });
}

// ── Number Formatting ────────────────────────────────
function fmtCurrency(val) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
}

// ── Animate KPI counter ──────────────────────────────
function animateCount(id, end, prefix = '$') {
  const el = document.getElementById(id);
  if (!el) return;
  const start = parseFloat(el.textContent.replace(/[^0-9.]/g,'')) || 0;
  const duration = 800;
  const startTime = performance.now();
  function update(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = (prefix || '') + ((start + (end - start) * eased).toFixed(2));
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// ── Page Fade-in ─────────────────────────────────────
document.querySelectorAll('.fade-up').forEach((el, i) => {
  el.style.animationDelay = `${i * 0.05}s`;
});
