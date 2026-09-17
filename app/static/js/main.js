// ── TOAST ─────────────────────────────────────────────────────────────────────

function showToast(message) {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:8px;max-width:300px';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.style.cssText = `
    background:#111; color:#fff; padding:12px 18px; border-radius:10px;
    font-size:0.85rem; font-weight:600; box-shadow:0 4px 20px rgba(0,0,0,0.15);
    border-left:3px solid #2ecc71; opacity:0; transition:opacity 0.3s;
    display:flex; align-items:center; gap:8px;
  `;
  toast.innerHTML = `<i class="bi bi-check-circle-fill" style="color:#2ecc71;font-size:1rem"></i>${message}`;
  container.appendChild(toast);
  requestAnimationFrame(() => { toast.style.opacity = '1'; });
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 2500);
}
