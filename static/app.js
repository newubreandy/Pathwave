/* ──────────────────────────────────────────────────────────────
   PathWave — Frontend App Logic
   ────────────────────────────────────────────────────────────── */

const API = '';   // same origin

// ── State ───────────────────────────────────────────────────────
let state = {
  email: '',
  code:  '',
  token: localStorage.getItem('pw_token') || '',
  step:  1,
  timerInterval: null,
  timerSeconds:  300,
};

// ── Utilities ────────────────────────────────────────────────────
function $(id) { return document.getElementById(id); }

function setLoading(btnId, loading) {
  const btn    = $(btnId);
  const text   = btn.querySelector('.btn-text');
  const loader = btn.querySelector('.btn-loader');
  btn.disabled = loading;
  text.style.display  = loading ? 'none' : '';
  loader.classList.toggle('hidden', !loading);
}

function showError(id, msg) {
  const el = $(id);
  if (!el) return;
  el.textContent = msg;
  if (msg) el.style.display = 'flex';
  else     el.style.display = '';
}

function clearErrors() {
  ['email-error','code-error','pw-error','login-error'].forEach(id => showError(id, ''));
}

// ── Step Navigation ──────────────────────────────────────────────
function goToStep(n) {
  for (let i = 1; i <= 4; i++) {
    const s = $(`form-step-${i}`);
    if (s) s.classList.toggle('hidden', i !== n);

    const stepEl = $(`step-${i}`);
    if (stepEl) {
      stepEl.classList.remove('active', 'done');
      if (i < n)  stepEl.classList.add('done');
      if (i === n) stepEl.classList.add('active');
    }
  }

  // Update step lines
  const lines = document.querySelectorAll('.step-line');
  lines.forEach((line, idx) => {
    line.classList.toggle('active', idx < n - 1);
  });

  state.step = n;
  clearErrors();
}

// ── Show/Hide Sections ───────────────────────────────────────────
function showSignup() {
  $('signup-section').classList.remove('hidden');
  $('login-section').classList.add('hidden');
  $('dashboard-section').classList.add('hidden');
  goToStep(1);
}

function showLogin() {
  $('signup-section').classList.add('hidden');
  $('login-section').classList.remove('hidden');
  $('dashboard-section').classList.add('hidden');
  clearErrors();
  $('login-email').value = '';
  $('login-pw').value = '';
}

function showDashboard() {
  $('signup-section').classList.add('hidden');
  $('login-section').classList.add('hidden');
  $('dashboard-section').classList.remove('hidden');

  const email = state.email || parseJwt(state.token)?.email || '사용자';
  $('dash-email').textContent = email;
  $('dash-greeting').textContent = `환영합니다! 🎉`;
  $('dash-avatar').textContent = email.charAt(0).toUpperCase();
}

function parseJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch { return null; }
}

// ── Step 1: Send Code ────────────────────────────────────────────
async function handleSendCode() {
  const email = $('email-input').value.trim();
  showError('email-error', '');

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    showError('email-error', '⚠ 올바른 이메일 주소를 입력해 주세요.');
    return;
  }

  setLoading('send-code-btn', true);
  try {
    const res  = await fetch(`${API}/api/auth/send-code`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email }),
    });
    const data = await res.json();

    if (data.success) {
      state.email = email;
      $('email-badge').textContent = email;
      goToStep(2);
      startTimer();
      $('code-0').focus();
    } else {
      showError('email-error', `⚠ ${data.message}`);
    }
  } catch (err) {
    showError('email-error', '⚠ 서버 연결에 실패했습니다. 잠시 후 다시 시도해 주세요.');
  } finally {
    setLoading('send-code-btn', false);
  }
}

// ── Step 2: Code Input ───────────────────────────────────────────
function onCodeInput(idx) {
  const box = $(`code-${idx}`);
  const val = box.value.replace(/\D/g,'');
  box.value = val;

  if (val.length === 1) {
    box.classList.add('filled');
    if (idx < 5) {
      $(`code-${idx+1}`).focus();
    } else {
      // Auto-verify when all 6 filled
      const allFilled = [0,1,2,3,4,5].every(i => $(`code-${i}`).value.length === 1);
      if (allFilled) handleVerifyCode();
    }
  } else {
    box.classList.remove('filled');
  }
}

function onCodeKeydown(e, idx) {
  if (e.key === 'Backspace' && !$(`code-${idx}`).value && idx > 0) {
    $(`code-${idx-1}`).focus();
    $(`code-${idx-1}`).value = '';
    $(`code-${idx-1}`).classList.remove('filled');
  }
  if (e.key === 'Enter') handleVerifyCode();
}

function getCode() {
  return [0,1,2,3,4,5].map(i => $(`code-${i}`).value).join('');
}

function clearCodeBoxes(shake = false) {
  for (let i = 0; i < 6; i++) {
    const box = $(`code-${i}`);
    if (shake) {
      box.classList.add('error');
      setTimeout(() => box.classList.remove('error'), 500);
    }
    box.value = '';
    box.classList.remove('filled');
  }
  if (!shake) $('code-0').focus();
}

// ── Timer ────────────────────────────────────────────────────────
function startTimer() {
  state.timerSeconds = 300;
  clearInterval(state.timerInterval);
  updateTimerDisplay();
  $('resend-link').classList.add('disabled');

  state.timerInterval = setInterval(() => {
    state.timerSeconds--;
    updateTimerDisplay();
    if (state.timerSeconds <= 0) {
      clearInterval(state.timerInterval);
      $('resend-link').classList.remove('disabled');
    }
  }, 1000);
}

function updateTimerDisplay() {
  const m = String(Math.floor(state.timerSeconds / 60)).padStart(2,'0');
  const s = String(state.timerSeconds % 60).padStart(2,'0');
  $('timer').textContent = `${m}:${s}`;
}

async function handleResend() {
  clearCodeBoxes();
  await handleSendCode();
}

// ── Step 2: Verify Code ──────────────────────────────────────────
async function handleVerifyCode() {
  const code = getCode();
  showError('code-error', '');

  if (code.length < 6) {
    showError('code-error', '⚠ 6자리 코드를 모두 입력해 주세요.');
    return;
  }

  setLoading('verify-code-btn', true);
  try {
    const res  = await fetch(`${API}/api/auth/verify-code`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email: state.email, code }),
    });
    const data = await res.json();

    if (data.success) {
      state.code = code;
      clearInterval(state.timerInterval);
      goToStep(3);
      $('pw-input').focus();
    } else {
      showError('code-error', `⚠ ${data.message}`);
      clearCodeBoxes(true);
    }
  } catch {
    showError('code-error', '⚠ 서버 오류가 발생했습니다.');
  } finally {
    setLoading('verify-code-btn', false);
  }
}

// ── Password Strength ────────────────────────────────────────────
function checkPwStrength() {
  const pw   = $('pw-input').value;
  const fill = $('pw-strength-fill');
  const lbl  = $('pw-strength-label');

  let score = 0;
  if (pw.length >= 8)  score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;

  const map = [
    { pct: '0%',   color: '',              text: '' },
    { pct: '20%',  color: 'var(--error)',  text: '매우 약함' },
    { pct: '40%',  color: '#f97316',       text: '약함' },
    { pct: '60%',  color: 'var(--warning)',text: '보통' },
    { pct: '80%',  color: '#84cc16',       text: '강함' },
    { pct: '100%', color: 'var(--success)',text: '매우 강함 🔒' },
  ];

  const level = score >= map.length ? map.length - 1 : score;
  fill.style.width  = map[level].pct;
  fill.style.background = map[level].color;
  lbl.textContent   = map[level].text;
  lbl.style.color   = map[level].color;

  checkPwMatch();
}

function checkPwMatch() {
  const pw  = $('pw-input').value;
  const pw2 = $('pw-confirm-input').value;
  const msg = $('pw-match-msg');

  if (!pw2) { msg.textContent = ''; return; }
  if (pw === pw2) {
    msg.textContent = '✓ 비밀번호가 일치합니다.';
    msg.style.color = 'var(--success)';
  } else {
    msg.textContent = '✗ 비밀번호가 일치하지 않습니다.';
    msg.style.color = 'var(--error)';
  }
}

// ── Step 3: Register ─────────────────────────────────────────────
async function handleRegister() {
  const pw  = $('pw-input').value;
  const pw2 = $('pw-confirm-input').value;
  showError('pw-error', '');

  if (!pw || pw.length < 8) {
    showError('pw-error', '⚠ 비밀번호는 최소 8자 이상이어야 합니다.');
    return;
  }
  if (pw !== pw2) {
    showError('pw-error', '⚠ 비밀번호가 일치하지 않습니다.');
    return;
  }

  setLoading('register-btn', true);
  try {
    const res  = await fetch(`${API}/api/auth/register`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email: state.email, code: state.code, password: pw }),
    });
    const data = await res.json();

    if (data.success) {
      state.token = data.token;
      localStorage.setItem('pw_token', data.token);
      $('success-email').textContent = state.email;
      goToStep(4);
    } else {
      showError('pw-error', `⚠ ${data.message}`);
    }
  } catch {
    showError('pw-error', '⚠ 서버 오류가 발생했습니다.');
  } finally {
    setLoading('register-btn', false);
  }
}

// ── Login ────────────────────────────────────────────────────────
async function handleLogin() {
  const email = $('login-email').value.trim();
  const pw    = $('login-pw').value;
  showError('login-error', '');

  if (!email || !pw) {
    showError('login-error', '⚠ 이메일과 비밀번호를 모두 입력해 주세요.');
    return;
  }

  setLoading('login-btn', true);
  try {
    const res  = await fetch(`${API}/api/auth/login`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email, password: pw }),
    });
    const data = await res.json();

    if (data.success) {
      state.token = data.token;
      state.email = data.user.email;
      localStorage.setItem('pw_token', data.token);
      showDashboard();
    } else {
      showError('login-error', `⚠ ${data.message}`);
    }
  } catch {
    showError('login-error', '⚠ 서버 오류가 발생했습니다.');
  } finally {
    setLoading('login-btn', false);
  }
}

// ── Password visibility toggle ────────────────────────────────────
function togglePw(inputId, btn) {
  const input = $(inputId);
  if (input.type === 'password') {
    input.type = 'text';
    btn.textContent = '🙈';
  } else {
    input.type = 'password';
    btn.textContent = '👁';
  }
}

// ── Logout ───────────────────────────────────────────────────────
function handleLogout() {
  state.token = '';
  state.email = '';
  localStorage.removeItem('pw_token');
  showSignup();
}

// ── Keyboard shortcut: Enter on email ────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  $('email-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') handleSendCode();
  });

  // Auto-login if token exists
  if (state.token) {
    const payload = parseJwt(state.token);
    if (payload && payload.exp * 1000 > Date.now()) {
      state.email = payload.email;
      showDashboard();
    } else {
      localStorage.removeItem('pw_token');
      state.token = '';
    }
  }
});
