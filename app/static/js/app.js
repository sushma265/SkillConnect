/* ═══════════════════════════════════════════════
   SkillConnect — app.js
   Single-page app: routing, API calls, rendering
   Updated: Glassmorphism + dual theme support
═══════════════════════════════════════════════ */

const BASE = '';

// ── State ─────────────────────────────────────
let token         = localStorage.getItem('sc_token') || null;
let currentUser   = JSON.parse(localStorage.getItem('sc_user') || 'null');
let allCourses    = [];
let allEvents     = [];
let currentRating = 0;

/* ─────────────────────────────────────────────
   THEME TOGGLE
───────────────────────────────────────────── */
function initTheme() {
  // Respect saved preference, default to dark
  const saved = localStorage.getItem('sc_theme') || 'dark';
  document.documentElement.dataset.theme = saved;
  updateThemeBtn(saved);
}

function toggleTheme() {
  const current = document.documentElement.dataset.theme;
  const next    = current === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  localStorage.setItem('sc_theme', next);
  updateThemeBtn(next);
}

function updateThemeBtn(theme) {
  const btn = document.getElementById('themeToggle');
  if (!btn) return;
  btn.textContent    = theme === 'dark' ? '☀️' : '🌙';
  btn.title          = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
  btn.setAttribute('aria-label', btn.title);
}

/* ─────────────────────────────────────────────
   LOADING SCREEN
───────────────────────────────────────────── */
window.addEventListener('DOMContentLoaded', () => {
  initTheme();
  const screen = document.getElementById('loadingScreen');
  if (!screen) return;
  setTimeout(() => {
    screen.classList.add('fade-out');
    setTimeout(() => screen.remove(), 600);
  }, 2000);
});

/* ─────────────────────────────────────────────
   NAVBAR SCROLL EFFECT
───────────────────────────────────────────── */
window.addEventListener('scroll', () => {
  const nav = document.getElementById('navbar');
  if (nav) nav.classList.toggle('scrolled', window.scrollY > 30);
});

/* ─────────────────────────────────────────────
   API HELPERS
───────────────────────────────────────────── */
async function api(method, path, body = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);
  const res  = await fetch(BASE + path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || data.msg || 'Request failed');
  return data;
}

const GET  = (p)    => api('GET',    p);
const POST = (p, b) => api('POST',   p, b);
const PUT  = (p, b) => api('PUT',    p, b);
const DEL  = (p)    => api('DELETE', p);

/* ─────────────────────────────────────────────
   TOAST
───────────────────────────────────────────── */
const TOAST_ICONS = { success: '✅', error: '❌', info: '⚡' };

function toast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span class="toast-icon">${TOAST_ICONS[type] || '⚡'}</span><span>${msg}</span>`;
  const container = document.getElementById('toastContainer');
  container.appendChild(el);
  setTimeout(() => {
    el.style.animation  = 'none';
    el.style.opacity    = '0';
    el.style.transform  = 'translateX(60px)';
    el.style.transition = 'all 0.3s ease';
    setTimeout(() => el.remove(), 300);
  }, 3200);
}

/* ─────────────────────────────────────────────
   PAGE ROUTING
───────────────────────────────────────────── */
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const el = document.getElementById(`page-${name}`);
  if (!el) return;
  el.classList.add('active');
  closeDropdown();
  closeMobileMenu();

  const loaders = {
    'home':             loadHome,
    'courses':          loadCourses,
    'events':           loadEvents,
    'announcements':    loadAnnouncements,
    'feedback-page':    loadFeedback,
    'my-registrations': loadMyRegistrations,
    'payment-history':  loadPaymentHistory,
    'admin-dashboard':  () => loadAdminTab('users', document.querySelector('.admin-tabs .tab')),
    'submit-feedback':  initFeedbackForm,
  };
  if (loaders[name]) loaders[name]();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* ─────────────────────────────────────────────
   AUTH
───────────────────────────────────────────── */
function updateNavForUser() {
  const authEl = document.getElementById('navAuth');
  const userEl = document.getElementById('navUser');

  if (currentUser) {
    authEl.classList.add('hidden');
    userEl.classList.remove('hidden');

    const avatarEl = document.getElementById('userAvatar');
    if (avatarEl) avatarEl.textContent = (currentUser.name || 'U').charAt(0).toUpperCase();
    document.getElementById('userBadgeName').textContent = currentUser.name;
    document.getElementById('userBadgeRole').textContent = currentUser.role;

    const ddName  = document.getElementById('dropdownUserName');
    const ddEmail = document.getElementById('dropdownUserEmail');
    if (ddName)  ddName.textContent  = currentUser.name;
    if (ddEmail) ddEmail.textContent = currentUser.email || '';

    document.getElementById('conductorLinks').classList.toggle('hidden', !['conductor','admin'].includes(currentUser.role));
    document.getElementById('adminLinks').classList.toggle('hidden', currentUser.role !== 'admin');
  } else {
    authEl.classList.remove('hidden');
    userEl.classList.add('hidden');
  }
}

async function login() {
  const email    = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;
  if (!email || !password) return toast('Please fill in all fields', 'error');
  try {
    const data  = await POST('/auth/login', { email, password });
    token       = data.access_token;
    currentUser = data.user;
    localStorage.setItem('sc_token', token);
    localStorage.setItem('sc_user', JSON.stringify(currentUser));
    updateNavForUser();
    toast(`Welcome back, ${currentUser.name}! ⚡`, 'success');
    showPage('home');
  } catch (e) { toast(e.message, 'error'); }
}

async function signup() {
  const name     = document.getElementById('signupName').value.trim();
  const email    = document.getElementById('signupEmail').value.trim();
  const password = document.getElementById('signupPassword').value;
  const role     = document.getElementById('signupRole').value;
  if (!name || !email || !password) return toast('Please fill in all fields', 'error');
  try {
    await POST('/auth/signup', { name, email, password, role });
    toast('Account created! Please sign in.', 'success');
    showPage('login');
  } catch (e) { toast(e.message, 'error'); }
}

function selectRole(role) {
  document.getElementById('signupRole').value = role;
}

function logout() {
  token = null; currentUser = null;
  localStorage.removeItem('sc_token');
  localStorage.removeItem('sc_user');
  updateNavForUser();
  toast("You've been logged out", 'info');
  showPage('home');
}

function requireLogin() {
  if (!token) { toast('Please login to continue', 'error'); showPage('login'); return false; }
  return true;
}

/* ─────────────────────────────────────────────
   HOME
───────────────────────────────────────────── */
async function loadHome() {
  try {
    const [cData, eData, aData] = await Promise.all([
      GET('/courses'), GET('/events'), GET('/announcements')
    ]);
    allCourses = cData.courses;
    allEvents  = eData.events;

    animateCounter('statCourses',       cData.courses.length);
    animateCounter('statEvents',        eData.events.length);
    animateCounter('statAnnouncements', aData.announcements.length);

    renderCourseCards(cData.courses.slice(0, 3), 'homeCoursesGrid');
    renderEventCards(eData.events.slice(0, 3),   'homeEventsGrid');
  } catch (e) { toast('Failed to load page data', 'error'); }
}

function animateCounter(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  let start   = 0;
  const step  = Math.ceil(target / (1200 / 16));
  const timer = setInterval(() => {
    start = Math.min(start + step, target);
    el.textContent = start;
    if (start >= target) clearInterval(timer);
  }, 16);
}

/* ─────────────────────────────────────────────
   COURSES
───────────────────────────────────────────── */
async function loadCourses() {
  document.getElementById('coursesGrid').innerHTML = loadingHTML();
  try {
    const data = await GET('/courses');
    allCourses = data.courses;
    renderCourseCards(allCourses, 'coursesGrid');
  } catch (e) { toast('Failed to load courses', 'error'); }
}

function filterCourses(q) {
  const filtered = allCourses.filter(c =>
    c.title.toLowerCase().includes(q.toLowerCase()) ||
    (c.category || '').toLowerCase().includes(q.toLowerCase())
  );
  renderCourseCards(filtered, 'coursesGrid');
}

function renderCourseCards(courses, gridId) {
  const grid = document.getElementById(gridId);
  if (!courses.length) {
    grid.innerHTML = emptyHTML('No courses found', 'Search for something else or check back later');
    return;
  }
  grid.innerHTML = courses.map(c => `
    <div class="card course-card" data-type="course">
      <div class="card-badges">
        <span class="card-type-badge badge-course">📚 Course</span>
        ${c.category ? `<span class="card-type-badge badge-category">${esc(c.category)}</span>` : ''}
      </div>
      <h3>${esc(c.title)}</h3>
      <p>${esc(c.description)}</p>
      <div class="card-meta">
        ${c.instructor ? `<span class="meta-item">👤 ${esc(c.instructor)}</span>` : ''}
        ${c.duration   ? `<span class="meta-item">⏱ ${esc(c.duration)}</span>`   : ''}
      </div>
      <div class="card-price">₹${c.price.toLocaleString('en-IN')} <small>/ course</small></div>
      <div class="card-actions">
        <button class="btn btn-ghost btn-sm" onclick="viewCourse(${c.id})">Details</button>
        <button class="btn btn-primary btn-sm" onclick="buyCourse(${c.id}, '${esc(c.title)}', ${c.price})">Enroll Now</button>
      </div>
      <!-- Progress reveal on hover -->
      <div class="card-reveal"><div class="prog" style="width:${Math.floor(Math.random()*60+25)}%"></div></div>
    </div>`).join('');
}

async function viewCourse(id) {
  try {
    const data = await GET(`/courses/${id}`);
    const c    = data.course;
    openModal(`
      <div class="card-badges" style="margin-bottom:0.75rem">
        <span class="card-type-badge badge-course">📚 Course</span>
        ${c.category ? `<span class="card-type-badge badge-category">${esc(c.category)}</span>` : ''}
      </div>
      <h2>${esc(c.title)}</h2>
      <div class="modal-detail">
        <div class="modal-detail-row"><span>Instructor</span><span>${esc(c.instructor || '–')}</span></div>
        <div class="modal-detail-row"><span>Duration</span><span>${esc(c.duration || '–')}</span></div>
        <div class="modal-detail-row"><span>Price</span><span style="font-weight:800;color:var(--text)">₹${c.price.toLocaleString('en-IN')}</span></div>
      </div>
      <p style="color:var(--text2);line-height:1.7;margin:1rem 0;font-size:0.9rem">${esc(c.description)}</p>
      <div class="modal-actions">
        <button class="btn btn-primary" onclick="buyCourse(${c.id},'${esc(c.title)}',${c.price});closeModal()">Enroll Now</button>
        ${canManageCourse(c) ? `<button class="btn btn-danger btn-sm" onclick="deleteCourse(${c.id})">Delete</button>` : ''}
      </div>
    `);
  } catch (e) { toast(e.message, 'error'); }
}

function canManageCourse(c) {
  if (!currentUser) return false;
  if (currentUser.role === 'admin') return true;
  if (currentUser.role === 'conductor' && c.created_by === currentUser.id) return true;
  return false;
}

async function buyCourse(id, title, price) {
  if (!requireLogin()) return;
  if (!confirm(`Enroll in "${title}" for ₹${price}?\n\n(Razorpay test mode — no real charge)`)) return;
  try {
    const order = await POST('/payments/create-order', { payment_type: 'course', item_id: id });
    toast('Order created! Opening payment…', 'info');
    await simulatePayment(order.order_id);
  } catch (e) { toast(e.message, 'error'); }
}

async function simulatePayment(orderId) {
  openModal(`
    <div style="text-align:center;padding:1rem 0">
      <div style="font-size:3rem;margin-bottom:1rem">💳</div>
      <h2 style="margin-bottom:0.5rem">Payment Order Created</h2>
      <p style="color:var(--text2);line-height:1.7;margin:1rem 0">
        Your Razorpay order has been created successfully.
      </p>
      <div style="background:var(--bg-glass3);border:1px solid var(--border);border-radius:var(--radius);padding:1rem;margin:1rem 0;text-align:left;backdrop-filter:blur(8px)">
        <div style="font-size:0.72rem;color:var(--text3);text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px">Order ID</div>
        <code>${orderId}</code>
      </div>
      <p style="font-size:0.82rem;color:var(--text3)">
        In production, the Razorpay checkout will open here. After payment,
        <code>POST /payments/verify</code> is called with the callback data.
      </p>
    </div>
    <div class="modal-actions" style="justify-content:center">
      <button class="btn btn-success" onclick="closeModal();toast('Payment flow complete! 🎉','success')">Got it</button>
    </div>
  `);
}

async function createCourse() {
  if (!requireLogin()) return;
  const body = {
    title:       document.getElementById('cTitle').value.trim(),
    description: document.getElementById('cDesc').value.trim(),
    price:       parseFloat(document.getElementById('cPrice').value),
    duration:    document.getElementById('cDuration').value.trim(),
    instructor:  document.getElementById('cInstructor').value.trim(),
    category:    document.getElementById('cCategory').value.trim(),
  };
  if (!body.title || !body.description || isNaN(body.price))
    return toast('Title, description and price are required', 'error');
  try {
    await POST('/courses', body);
    toast('Course published successfully! 🎉', 'success');
    ['cTitle','cDesc','cPrice','cDuration','cInstructor','cCategory'].forEach(id =>
      document.getElementById(id).value = '');
    showPage('courses');
  } catch (e) { toast(e.message, 'error'); }
}

async function deleteCourse(id) {
  if (!confirm('Delete this course permanently?')) return;
  try {
    await DEL(`/courses/${id}`);
    toast('Course deleted', 'success');
    closeModal(); loadCourses();
  } catch (e) { toast(e.message, 'error'); }
}

/* ─────────────────────────────────────────────
   EVENTS
───────────────────────────────────────────── */
async function loadEvents() {
  document.getElementById('eventsGrid').innerHTML = loadingHTML();
  try {
    const data = await GET('/events');
    allEvents  = data.events;
    renderEventCards(allEvents, 'eventsGrid');
  } catch (e) { toast('Failed to load events', 'error'); }
}

function filterEvents(type, tabEl) {
  document.querySelectorAll('.filter-tabs .tab').forEach(t => t.classList.remove('active'));
  tabEl.classList.add('active');
  const filtered = type === 'all' ? allEvents : allEvents.filter(e => e.event_type === type);
  renderEventCards(filtered, 'eventsGrid');
}

function renderEventCards(events, gridId) {
  const grid = document.getElementById(gridId);
  if (!events.length) {
    grid.innerHTML = emptyHTML('No events found', 'Check back soon for upcoming events');
    return;
  }
  grid.innerHTML = events.map(e => {
    const isFree     = e.price === 0;
    const isWorkshop = e.event_type === 'workshop';
    const badgeClass = isWorkshop ? 'badge-workshop' : 'badge-event';
    const badgeIcon  = isWorkshop ? '🔧' : '🎯';
    const date = new Date(e.event_date).toLocaleDateString('en-IN', { day:'numeric', month:'short', year:'numeric' });
    const pct  = Math.round((e.registered_count / e.capacity) * 100);
    const barColor = pct > 80
      ? 'var(--danger)'
      : pct > 50
        ? 'var(--warning)'
        : 'var(--blue)';
    // Days until event
    const daysUntil = Math.ceil((new Date(e.event_date) - Date.now()) / 86400000);
    const countdownText = daysUntil > 0
      ? `${daysUntil} day${daysUntil !== 1 ? 's' : ''} to go`
      : daysUntil === 0
        ? 'Today!'
        : 'Event passed';

    return `
    <div class="card event-card" data-type="event">
      <div class="card-badges">
        <span class="card-type-badge ${badgeClass}">${badgeIcon} ${e.event_type}</span>
        <span class="card-type-badge ${isFree ? 'badge-free' : 'badge-paid'}">${isFree ? '🆓 FREE' : '₹' + e.price.toLocaleString('en-IN')}</span>
      </div>
      <h3>${esc(e.title)}</h3>
      <p>${esc(e.description)}</p>
      <div class="card-meta">
        <span class="meta-item">📅 ${date}</span>
        ${e.venue ? `<span class="meta-item">📍 ${esc(e.venue)}</span>` : ''}
        <span class="meta-item">👥 ${e.registered_count}/${e.capacity}</span>
      </div>
      <div style="margin-bottom:1.25rem">
        <div style="display:flex;justify-content:space-between;font-size:0.72rem;color:var(--text3);margin-bottom:5px">
          <span>Seats filled</span><span>${pct}%</span>
        </div>
        <div style="height:4px;background:var(--border);border-radius:2px;overflow:hidden;backdrop-filter:blur(4px)">
          <div style="width:${pct}%;height:100%;background:${barColor};border-radius:2px;transition:width 0.6s ease;box-shadow:0 0 8px ${barColor}44"></div>
        </div>
      </div>
      <!-- Countdown reveal on hover -->
      <div class="evt-reveal"><div class="pulse-dot"></div>${countdownText}</div>
      <div class="card-actions">
        <button class="btn btn-ghost btn-sm" onclick="viewEvent(${e.id})">Details</button>
        <button class="btn btn-primary btn-sm" onclick="registerEvent(${e.id},'${esc(e.title)}',${e.price})">Register</button>
      </div>
    </div>`;
  }).join('');
}

async function viewEvent(id) {
  try {
    const data = await GET(`/events/${id}`);
    const e    = data.event;
    const date = new Date(e.event_date).toLocaleString('en-IN', { dateStyle: 'long', timeStyle: 'short' });
    const isWorkshop = e.event_type === 'workshop';
    openModal(`
      <div class="card-badges" style="margin-bottom:0.75rem">
        <span class="card-type-badge ${isWorkshop ? 'badge-workshop' : 'badge-event'}">${isWorkshop ? '🔧' : '🎯'} ${e.event_type}</span>
        <span class="card-type-badge ${e.price === 0 ? 'badge-free' : 'badge-paid'}">${e.price === 0 ? '🆓 FREE' : '₹' + e.price}</span>
      </div>
      <h2>${esc(e.title)}</h2>
      <div class="modal-detail">
        <div class="modal-detail-row"><span>Date &amp; Time</span><span>${date}</span></div>
        <div class="modal-detail-row"><span>Venue</span><span>${esc(e.venue || '–')}</span></div>
        <div class="modal-detail-row"><span>Capacity</span><span>${e.registered_count}/${e.capacity} registered</span></div>
      </div>
      <p style="color:var(--text2);line-height:1.7;margin:1rem 0;font-size:0.9rem">${esc(e.description)}</p>
      <div class="modal-actions">
        <button class="btn btn-primary" onclick="registerEvent(${e.id},'${esc(e.title)}',${e.price});closeModal()">Register Now</button>
        ${canManageEvent(e) ? `<button class="btn btn-danger btn-sm" onclick="deleteEvent(${e.id})">Delete</button>` : ''}
      </div>
    `);
  } catch (e) { toast(e.message, 'error'); }
}

function canManageEvent(e) {
  if (!currentUser) return false;
  if (currentUser.role === 'admin') return true;
  if (currentUser.role === 'conductor' && e.created_by === currentUser.id) return true;
  return false;
}

async function registerEvent(id, title, price) {
  if (!requireLogin()) return;
  try {
    if (price > 0) {
      const order = await POST('/payments/create-order', { payment_type: 'event', item_id: id });
      toast('Payment order created!', 'info');
      await simulatePayment(order.order_id);
    } else {
      await POST(`/events/${id}/register`, {});
      toast(`Registered for "${title}"! 🎉`, 'success');
    }
  } catch (e) { toast(e.message, 'error'); }
}

async function createEvent() {
  if (!requireLogin()) return;
  const body = {
    title:       document.getElementById('eTitle').value.trim(),
    description: document.getElementById('eDesc').value.trim(),
    event_type:  document.getElementById('eType').value,
    event_date:  document.getElementById('eDate').value.trim(),
    venue:       document.getElementById('eVenue').value.trim(),
    price:       parseFloat(document.getElementById('ePrice').value) || 0,
    capacity:    parseInt(document.getElementById('eCapacity').value) || 100,
  };
  if (!body.title || !body.description || !body.event_date)
    return toast('Title, description and date are required', 'error');
  try {
    await POST('/events', body);
    toast('Event created! 🎉', 'success');
    showPage('events');
  } catch (e) { toast(e.message, 'error'); }
}

async function deleteEvent(id) {
  if (!confirm('Delete this event?')) return;
  try {
    await DEL(`/events/${id}`);
    toast('Event deleted', 'success');
    closeModal(); loadEvents();
  } catch (e) { toast(e.message, 'error'); }
}

/* ─────────────────────────────────────────────
   ANNOUNCEMENTS
───────────────────────────────────────────── */
async function loadAnnouncements() {
  document.getElementById('announcementsList').innerHTML = loadingHTML();
  try {
    const data = await GET('/announcements');
    const list = document.getElementById('announcementsList');
    if (!data.announcements.length) {
      list.innerHTML = emptyHTML('No announcements yet', 'Check back later for updates');
      return;
    }
    list.innerHTML = data.announcements.map((a, i) => `
      <div class="list-item" style="animation-delay:${i * 0.05}s">
        <div class="list-item-header">
          <div style="display:flex;align-items:center;gap:10px">
            <div style="width:36px;height:36px;background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.2);border-radius:var(--radius-sm);display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0;backdrop-filter:blur(8px)">📢</div>
            <h3>${esc(a.title)}</h3>
          </div>
          <span class="meta-item" style="font-size:0.75rem;white-space:nowrap">${timeAgo(a.created_at)}</span>
        </div>
        <p style="padding-left:46px">${esc(a.content)}</p>
      </div>`).join('');
  } catch (e) { toast('Failed to load announcements', 'error'); }
}

async function createAnnouncement() {
  if (!requireLogin()) return;
  const body = {
    title:   document.getElementById('annTitle').value.trim(),
    content: document.getElementById('annContent').value.trim(),
  };
  if (!body.title || !body.content) return toast('Title and content are required', 'error');
  try {
    await POST('/announcements', body);
    toast('Announcement posted!', 'success');
    document.getElementById('annTitle').value   = '';
    document.getElementById('annContent').value = '';
    showPage('announcements');
  } catch (e) { toast(e.message, 'error'); }
}

/* ─────────────────────────────────────────────
   FEEDBACK
───────────────────────────────────────────── */
const RATING_LABELS = ['', 'Poor', 'Fair', 'Good', 'Great', 'Excellent'];

async function loadFeedback() {
  document.getElementById('feedbackList').innerHTML = loadingHTML();
  try {
    const data = await GET('/feedback');
    const list = document.getElementById('feedbackList');
    if (!data.feedback.length) {
      list.innerHTML = emptyHTML('No feedback yet', 'Be the first to share your experience');
      return;
    }
    list.innerHTML = data.feedback.map(f => {
      const stars = '★'.repeat(f.rating) + '☆'.repeat(5 - f.rating);
      return `
      <div class="list-item">
        <div class="list-item-header">
          <div>
            <span style="color:var(--blue);font-size:1.1rem;letter-spacing:2px">${stars}</span>
            <span style="color:var(--text3);font-size:0.8rem;margin-left:8px">${RATING_LABELS[f.rating] || ''}</span>
          </div>
          <span class="card-type-badge ${f.feedback_type === 'course' ? 'badge-course' : 'badge-event'}">${f.feedback_type === 'course' ? '📚' : '🎯'} ${f.feedback_type}</span>
        </div>
        ${f.comment ? `<p>${esc(f.comment)}</p>` : '<p style="color:var(--text3);font-style:italic">No comment provided</p>'}
        <div class="list-item-meta">
          <span>User #${f.user_id}</span>
          <span>${timeAgo(f.created_at)}</span>
        </div>
      </div>`;
    }).join('');
  } catch (e) { toast('Failed to load feedback', 'error'); }
}

async function initFeedbackForm() {
  if (!requireLogin()) return;
  await loadFeedbackItems();
}

async function loadFeedbackItems() {
  const type = document.getElementById('fbType').value;
  const sel  = document.getElementById('fbItem');
  sel.innerHTML = '<option value="">Loading…</option>';
  try {
    if (type === 'course') {
      const data = await GET('/courses');
      sel.innerHTML = data.courses.length
        ? data.courses.map(c => `<option value="${c.id}">${esc(c.title)}</option>`).join('')
        : '<option value="">No courses available</option>';
    } else {
      const data = await GET('/events');
      sel.innerHTML = data.events.length
        ? data.events.map(e => `<option value="${e.id}">${esc(e.title)}</option>`).join('')
        : '<option value="">No events available</option>';
    }
  } catch (e) { toast('Failed to load items', 'error'); }
}

function setRating(n) {
  currentRating = n;
  document.getElementById('fbRating').value = n;
  document.querySelectorAll('.star-btn').forEach((s, i) => s.classList.toggle('lit', i < n));
  const lbl = document.getElementById('ratingLabel');
  if (lbl) lbl.textContent = RATING_LABELS[n] ? `${RATING_LABELS[n]} (${n}/5)` : 'Click to rate';
}

async function submitFeedback() {
  if (!requireLogin()) return;
  const body = {
    feedback_type: document.getElementById('fbType').value,
    item_id:       parseInt(document.getElementById('fbItem').value),
    rating:        currentRating,
    comment:       document.getElementById('fbComment').value.trim(),
  };
  if (!body.rating)  return toast('Please select a star rating', 'error');
  if (!body.item_id) return toast('Please select an item', 'error');
  try {
    await POST('/feedback', body);
    toast('Feedback submitted! Thank you ⭐', 'success');
    showPage('feedback-page');
  } catch (e) { toast(e.message, 'error'); }
}

/* ─────────────────────────────────────────────
   MY REGISTRATIONS
───────────────────────────────────────────── */
async function loadMyRegistrations() {
  if (!requireLogin()) return;
  document.getElementById('myRegistrationsList').innerHTML = loadingHTML();
  try {
    const data = await GET('/events/my-registrations');
    const list = document.getElementById('myRegistrationsList');
    if (!data.registrations.length) {
      list.innerHTML = emptyHTML('No registrations yet', 'Browse events and register to see them here');
      return;
    }
    list.innerHTML = data.registrations.map(r => `
      <div class="list-item">
        <div class="list-item-header">
          <div style="display:flex;align-items:center;gap:10px">
            <div style="width:36px;height:36px;background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.2);border-radius:var(--radius-sm);display:flex;align-items:center;justify-content:center;font-size:1rem;backdrop-filter:blur(8px)">🎯</div>
            <h3>${esc(r.event_title || 'Event #' + r.event_id)}</h3>
          </div>
          <span class="status-pill status-${r.status}">${r.status}</span>
        </div>
        <div class="list-item-meta">
          <span>Registration #${r.id}</span>
          <span>${timeAgo(r.registered_at)}</span>
        </div>
      </div>`).join('');
  } catch (e) { toast(e.message, 'error'); }
}

/* ─────────────────────────────────────────────
   PAYMENT HISTORY
───────────────────────────────────────────── */
async function loadPaymentHistory() {
  if (!requireLogin()) return;
  document.getElementById('paymentHistoryList').innerHTML = loadingHTML();
  try {
    const data  = await GET('/payments/history');
    const list  = document.getElementById('paymentHistoryList');
    if (!data.payments.length) {
      list.innerHTML = emptyHTML('No payments yet', 'Your transactions will appear here');
      return;
    }

    const total       = data.payments.filter(p => p.status === 'paid').reduce((s, p) => s + p.amount, 0);
    const summaryHTML = `
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin-bottom:1.5rem">
        <div class="stat-card"><div class="num">${data.payments.length}</div><div class="lbl">Total Orders</div></div>
        <div class="stat-card"><div class="num">${data.payments.filter(p => p.status === 'paid').length}</div><div class="lbl">Completed</div></div>
        <div class="stat-card"><div class="num" style="background:var(--brand-grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">₹${total.toLocaleString('en-IN')}</div><div class="lbl">Total Spent</div></div>
      </div>`;

    list.innerHTML = summaryHTML + data.payments.map(p => `
      <div class="list-item">
        <div class="list-item-header">
          <div style="display:flex;align-items:center;gap:10px">
            <div style="width:36px;height:36px;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);border-radius:var(--radius-sm);display:flex;align-items:center;justify-content:center;font-size:1rem;backdrop-filter:blur(8px)">💳</div>
            <div>
              <h3>₹${p.amount.toLocaleString('en-IN')}</h3>
              <div style="font-size:0.78rem;color:var(--text3);margin-top:1px;text-transform:capitalize">${p.payment_type} payment</div>
            </div>
          </div>
          <span class="status-pill status-${p.status}">${p.status}</span>
        </div>
        <div class="list-item-meta">
          <span>Order: <code>${p.razorpay_order_id}</code></span>
          <span>${timeAgo(p.created_at)}</span>
        </div>
      </div>`).join('');
  } catch (e) { toast(e.message, 'error'); }
}

/* ─────────────────────────────────────────────
   ADMIN DASHBOARD
───────────────────────────────────────────── */
async function loadAdminTab(tab, tabEl) {
  document.querySelectorAll('.admin-tabs .tab').forEach(t => t.classList.remove('active'));
  if (tabEl) tabEl.classList.add('active');
  else document.querySelectorAll('.admin-tabs .tab')[0]?.classList.add('active');

  const content = document.getElementById('adminContent');
  content.innerHTML = loadingHTML();

  try {
    if (tab === 'users') {
      const data = await GET('/admin/users');
      const roleColor = {
        admin:     'var(--cyan)',
        conductor: 'var(--blue)',
        user:      'var(--indigo)'
      };
      content.innerHTML = `
        <div class="stats-row" style="margin-bottom:1.5rem">
          <div class="stat-card"><div class="num">${data.users.length}</div><div class="lbl">Total Users</div></div>
          <div class="stat-card"><div class="num">${data.users.filter(u => u.is_active).length}</div><div class="lbl">Active</div></div>
          <div class="stat-card"><div class="num">${data.users.filter(u => u.role === 'conductor').length}</div><div class="lbl">Conductors</div></div>
        </div>
        <div class="admin-table-wrap">
          <table>
            <thead><tr><th>User</th><th>Email</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>${data.users.map(u => `
              <tr>
                <td>
                  <div style="display:flex;align-items:center;gap:8px">
                    <div style="width:32px;height:32px;border-radius:50%;background:var(--brand-grad);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.8rem;color:#fff;flex-shrink:0;box-shadow:0 0 10px rgba(59,130,246,0.3)">${(u.name || '?').charAt(0).toUpperCase()}</div>
                    <span style="color:var(--text)">${esc(u.name)}</span>
                  </div>
                </td>
                <td>${esc(u.email)}</td>
                <td><span class="status-pill" style="background:${(roleColor[u.role] || 'var(--blue)')}22;color:${roleColor[u.role] || 'var(--blue)'};border-color:${(roleColor[u.role] || 'var(--blue)')}44">${u.role}</span></td>
                <td>${u.is_active ? '<span class="status-pill status-confirmed">active</span>' : '<span class="status-pill status-failed">inactive</span>'}</td>
                <td>
                  <div class="admin-actions">
                    <button class="btn btn-sm btn-ghost" onclick="adminToggleUser(${u.id},${!u.is_active})">${u.is_active ? 'Deactivate' : 'Activate'}</button>
                    <button class="btn btn-sm btn-danger" onclick="adminDeleteUser(${u.id})">Delete</button>
                  </div>
                </td>
              </tr>`).join('')}
            </tbody>
          </table>
        </div>`;

    } else if (tab === 'courses') {
      const data = await GET('/admin/courses');
      content.innerHTML = `
        <div class="admin-table-wrap">
          <table>
            <thead><tr><th>Title</th><th>Category</th><th>Price</th><th>Actions</th></tr></thead>
            <tbody>${data.courses.map(c => `
              <tr>
                <td style="color:var(--text);font-weight:500">${esc(c.title)}</td>
                <td>${c.category ? `<span class="card-type-badge badge-category">${esc(c.category)}</span>` : '–'}</td>
                <td style="color:var(--blue-light);font-weight:600">₹${c.price.toLocaleString('en-IN')}</td>
                <td><button class="btn btn-sm btn-danger" onclick="adminDeleteCourse(${c.id})">Delete</button></td>
              </tr>`).join('')}
            </tbody>
          </table>
        </div>`;

    } else if (tab === 'events') {
      const data = await GET('/admin/events');
      content.innerHTML = `
        <div class="admin-table-wrap">
          <table>
            <thead><tr><th>Title</th><th>Type</th><th>Date</th><th>Price</th><th>Registered</th><th>Actions</th></tr></thead>
            <tbody>${data.events.map(e => `
              <tr>
                <td style="color:var(--text);font-weight:500">${esc(e.title)}</td>
                <td><span class="card-type-badge ${e.event_type === 'workshop' ? 'badge-workshop' : 'badge-event'}">${e.event_type}</span></td>
                <td>${new Date(e.event_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</td>
                <td>${e.price === 0 ? '<span style="color:var(--success)">FREE</span>' : '<span style="color:var(--blue-light)">₹' + e.price.toLocaleString('en-IN') + '</span>'}</td>
                <td>${e.registered_count}/${e.capacity}</td>
                <td><button class="btn btn-sm btn-danger" onclick="adminDeleteEvent(${e.id})">Delete</button></td>
              </tr>`).join('')}
            </tbody>
          </table>
        </div>`;

    } else if (tab === 'payments') {
      const data = await GET('/admin/payments');
      const paid = data.payments.filter(p => p.status === 'paid');
      content.innerHTML = `
        <div class="stats-row">
          <div class="stat-card"><div class="num">${data.payments.length}</div><div class="lbl">Total Orders</div></div>
          <div class="stat-card"><div class="num" style="color:var(--success)">${paid.length}</div><div class="lbl">Paid</div></div>
          <div class="stat-card"><div class="num" style="background:var(--brand-grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">₹${(data.total_revenue || 0).toLocaleString('en-IN')}</div><div class="lbl">Revenue</div></div>
          <div class="stat-card"><div class="num" style="color:var(--danger)">${data.payments.length - paid.length}</div><div class="lbl">Pending</div></div>
        </div>
        <div class="admin-table-wrap">
          <table>
            <thead><tr><th>User</th><th>Type</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead>
            <tbody>${data.payments.map(p => `
              <tr>
                <td>#${p.user_id}</td>
                <td style="text-transform:capitalize">${p.payment_type}</td>
                <td style="color:var(--blue-light);font-weight:600">₹${p.amount.toLocaleString('en-IN')}</td>
                <td><span class="status-pill status-${p.status}">${p.status}</span></td>
                <td>${timeAgo(p.created_at)}</td>
              </tr>`).join('')}
            </tbody>
          </table>
        </div>`;
    }
  } catch (e) {
    content.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><h3>Error loading data</h3><p>${esc(e.message)}</p></div>`;
  }
}

async function adminToggleUser(id, active) {
  try {
    await PUT(`/admin/users/${id}`, { is_active: active });
    toast(`User ${active ? 'activated' : 'deactivated'}`, 'success');
    loadAdminTab('users', null);
  } catch (e) { toast(e.message, 'error'); }
}
async function adminDeleteUser(id) {
  if (!confirm('Delete this user permanently?')) return;
  try { await DEL(`/admin/users/${id}`); toast('User deleted', 'success'); loadAdminTab('users', null); }
  catch (e) { toast(e.message, 'error'); }
}
async function adminDeleteCourse(id) {
  if (!confirm('Delete this course?')) return;
  try { await DEL(`/admin/courses/${id}`); toast('Course deleted', 'success'); loadAdminTab('courses', null); }
  catch (e) { toast(e.message, 'error'); }
}
async function adminDeleteEvent(id) {
  if (!confirm('Delete this event?')) return;
  try { await DEL(`/admin/events/${id}`); toast('Event deleted', 'success'); loadAdminTab('events', null); }
  catch (e) { toast(e.message, 'error'); }
}

/* ─────────────────────────────────────────────
   MODAL
───────────────────────────────────────────── */
function openModal(html) {
  document.getElementById('modalContent').innerHTML = html;
  document.getElementById('modalOverlay').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}
function closeModal() {
  document.getElementById('modalOverlay').classList.add('hidden');
  document.body.style.overflow = '';
}

/* ─────────────────────────────────────────────
   DROPDOWN
───────────────────────────────────────────── */
function toggleDropdown() {
  document.getElementById('dropdownMenu').classList.toggle('open');
}
function closeDropdown() {
  document.getElementById('dropdownMenu')?.classList.remove('open');
}
document.addEventListener('click', e => {
  if (!e.target.closest('.dropdown')) closeDropdown();
});

/* ─────────────────────────────────────────────
   MOBILE MENU
───────────────────────────────────────────── */
function toggleMobileMenu()  { document.getElementById('mobileMenu').classList.toggle('open'); }
function closeMobileMenu()   { document.getElementById('mobileMenu')?.classList.remove('open'); }

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closeModal(); closeDropdown(); closeMobileMenu(); }
});

/* ─────────────────────────────────────────────
   HELPERS
───────────────────────────────────────────── */
function esc(str) {
  if (!str && str !== 0) return '';
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function loadingHTML() {
  return `
    <div class="loading">
      <div class="page-spinner">
        <svg viewBox="0 0 32 40" fill="none">
          <path d="M19 2L4 22H14L12 38L28 18H18L19 2Z" fill="url(#sp)"/>
          <defs>
            <linearGradient id="sp" x1="4" y1="2" x2="28" y2="38">
              <stop stop-color="#3b82f6"/><stop offset="1" stop-color="#06b6d4"/>
            </linearGradient>
          </defs>
        </svg>
      </div>
      <span>Loading…</span>
    </div>`;
}

function emptyHTML(title, subtitle = '') {
  return `
    <div class="empty-state">
      <div class="empty-icon">📭</div>
      <h3>${esc(title)}</h3>
      ${subtitle ? `<p>${esc(subtitle)}</p>` : ''}
    </div>`;
}

function timeAgo(dateStr) {
  const diff   = Date.now() - new Date(dateStr).getTime();
  const secs   = Math.floor(diff / 1000);
  const mins   = Math.floor(diff / 60000);
  const hours  = Math.floor(diff / 3600000);
  const days   = Math.floor(diff / 86400000);
  const weeks  = Math.floor(days / 7);
  const months = Math.floor(days / 30);
  if (secs < 30)  return 'just now';
  if (mins < 1)   return `${secs}s ago`;
  if (mins < 60)  return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7)   return `${days}d ago`;
  if (weeks < 5)  return `${weeks}w ago`;
  return `${months}mo ago`;
}

/* ─────────────────────────────────────────────
   BOOT
───────────────────────────────────────────── */
updateNavForUser();
showPage('home');