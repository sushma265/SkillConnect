/* ═══════════════════════════════════════════════════
   SkillConnect – Frontend Application
   Single-page app logic: routing, API calls, rendering
═══════════════════════════════════════════════════ */

const BASE = '';   // same origin — Flask serves API + HTML

// ── State ─────────────────────────────────────────
let token = localStorage.getItem('sc_token') || null;
let currentUser = JSON.parse(localStorage.getItem('sc_user') || 'null');
let allCourses = [];
let allEvents  = [];
let currentRating = 0;

// ═══════════════════════════════════════════════════
// API HELPERS
// ═══════════════════════════════════════════════════
async function api(method, path, body = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(BASE + path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || data.msg || 'Request failed');
  return data;
}

const GET  = (p)    => api('GET',    p);
const POST = (p, b) => api('POST',   p, b);
const PUT  = (p, b) => api('PUT',    p, b);
const DEL  = (p)    => api('DELETE', p);

// ═══════════════════════════════════════════════════
// TOAST
// ═══════════════════════════════════════════════════
function toast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  document.getElementById('toastContainer').appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ═══════════════════════════════════════════════════
// PAGE ROUTING
// ═══════════════════════════════════════════════════
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const el = document.getElementById(`page-${name}`);
  if (!el) return;
  el.classList.add('active');
  closeDropdown();

  // load data for the page
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
  window.scrollTo(0, 0);
}

// ═══════════════════════════════════════════════════
// AUTH
// ═══════════════════════════════════════════════════
function updateNavForUser() {
  const authEl = document.getElementById('navAuth');
  const userEl = document.getElementById('navUser');
  if (currentUser) {
    authEl.classList.add('hidden');
    userEl.classList.remove('hidden');
    document.getElementById('userBadgeRole').textContent = currentUser.role;
    document.getElementById('userBadgeName').textContent = currentUser.name;
    // show role-specific nav items
    const conductorLinks = document.getElementById('conductorLinks');
    const adminLinks     = document.getElementById('adminLinks');
    conductorLinks.classList.toggle('hidden', !['conductor','admin'].includes(currentUser.role));
    adminLinks.classList.toggle('hidden', currentUser.role !== 'admin');
  } else {
    authEl.classList.remove('hidden');
    userEl.classList.add('hidden');
  }
}

async function login() {
  const email    = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;
  if (!email || !password) return toast('Fill in all fields', 'error');
  try {
    const data = await POST('/auth/login', { email, password });
    token = data.access_token;
    currentUser = data.user;
    localStorage.setItem('sc_token', token);
    localStorage.setItem('sc_user', JSON.stringify(currentUser));
    updateNavForUser();
    toast(`Welcome back, ${currentUser.name}!`, 'success');
    showPage('home');
  } catch (e) { toast(e.message, 'error'); }
}

async function signup() {
  const name     = document.getElementById('signupName').value.trim();
  const email    = document.getElementById('signupEmail').value.trim();
  const password = document.getElementById('signupPassword').value;
  const role     = document.getElementById('signupRole').value;
  if (!name || !email || !password) return toast('Fill in all fields', 'error');
  try {
    await POST('/auth/signup', { name, email, password, role });
    toast('Account created! Please login.', 'success');
    showPage('login');
  } catch (e) { toast(e.message, 'error'); }
}

function logout() {
  token = null; currentUser = null;
  localStorage.removeItem('sc_token');
  localStorage.removeItem('sc_user');
  updateNavForUser();
  toast('Logged out', 'info');
  showPage('home');
}

function requireLogin() {
  if (!token) { toast('Please login first', 'error'); showPage('login'); return false; }
  return true;
}

// ═══════════════════════════════════════════════════
// HOME
// ═══════════════════════════════════════════════════
async function loadHome() {
  try {
    const [cData, eData, aData] = await Promise.all([
      GET('/courses'), GET('/events'), GET('/announcements')
    ]);
    allCourses = cData.courses;
    allEvents  = eData.events;

    document.getElementById('statCourses').textContent = cData.courses.length;
    document.getElementById('statEvents').textContent  = eData.events.length;
    document.getElementById('statAnnouncements').textContent = aData.announcements.length;

    renderCourseCards(cData.courses.slice(0, 3), 'homeCoursesGrid');
    renderEventCards(eData.events.slice(0, 3), 'homeEventsGrid');
  } catch(e) { toast('Failed to load home data', 'error'); }
}

// ═══════════════════════════════════════════════════
// COURSES
// ═══════════════════════════════════════════════════
async function loadCourses() {
  document.getElementById('coursesGrid').innerHTML = loadingHTML();
  try {
    const data = await GET('/courses');
    allCourses = data.courses;
    renderCourseCards(allCourses, 'coursesGrid');
  } catch(e) { toast('Failed to load courses', 'error'); }
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
  if (!courses.length) { grid.innerHTML = emptyHTML('No courses found'); return; }
  grid.innerHTML = courses.map(c => `
    <div class="card">
      <span class="card-type-badge badge-course">Course</span>
      ${c.category ? `<span class="card-type-badge badge-paid" style="margin-left:6px">${c.category}</span>` : ''}
      <h3>${esc(c.title)}</h3>
      <p>${esc(c.description)}</p>
      <div class="card-meta">
        ${c.instructor ? `<span class="meta-item">👤 ${esc(c.instructor)}</span>` : ''}
        ${c.duration   ? `<span class="meta-item">⏱ ${esc(c.duration)}</span>`   : ''}
      </div>
      <div class="card-price">₹${c.price.toLocaleString()} <small>/ course</small></div>
      <div class="card-actions">
        <button class="btn btn-ghost btn-sm" onclick="viewCourse(${c.id})">Details</button>
        <button class="btn btn-primary btn-sm" onclick="buyCourse(${c.id}, '${esc(c.title)}', ${c.price})">Buy Now</button>
      </div>
    </div>`).join('');
}

async function viewCourse(id) {
  try {
    const data = await GET(`/courses/${id}`);
    const c = data.course;
    openModal(`
      <h2>${esc(c.title)}</h2>
      <div class="modal-detail">
        <div class="modal-detail-row"><span>Category</span><span>${esc(c.category||'–')}</span></div>
        <div class="modal-detail-row"><span>Instructor</span><span>${esc(c.instructor||'–')}</span></div>
        <div class="modal-detail-row"><span>Duration</span><span>${esc(c.duration||'–')}</span></div>
        <div class="modal-detail-row"><span>Price</span><span>₹${c.price.toLocaleString()}</span></div>
      </div>
      <p style="color:var(--text2);line-height:1.7;margin:1rem 0">${esc(c.description)}</p>
      <div class="modal-actions">
        <button class="btn btn-primary" onclick="buyCourse(${c.id},'${esc(c.title)}',${c.price});closeModal()">Buy Now</button>
        ${canManageCourse(c) ? `
          <button class="btn btn-ghost" onclick="closeModal();showEditCourseModal(${c.id})">Edit</button>
          <button class="btn btn-danger" onclick="deleteCourse(${c.id})">Delete</button>
        ` : ''}
      </div>
    `);
  } catch(e) { toast(e.message, 'error'); }
}

function canManageCourse(c) {
  if (!currentUser) return false;
  if (currentUser.role === 'admin') return true;
  if (currentUser.role === 'conductor' && c.created_by === currentUser.id) return true;
  return false;
}

async function buyCourse(id, title, price) {
  if (!requireLogin()) return;
  if (!confirm(`Purchase "${title}" for ₹${price}?\n\n(Razorpay test mode — no real charge)`)) return;
  try {
    const order = await POST('/payments/create-order', { payment_type: 'course', item_id: id });
    // In test mode: auto-verify with dummy signature
    toast('Order created! Simulating payment…', 'info');
    await simulatePayment(order.order_id);
  } catch(e) { toast(e.message, 'error'); }
}

async function simulatePayment(orderId) {
  // For testing without a real Razorpay key, we just show success info
  openModal(`
    <h2>💳 Payment Order Created</h2>
    <p style="color:var(--text2);margin:1rem 0;line-height:1.7">
      Your Razorpay order has been created.<br><br>
      <strong>Order ID:</strong> <code style="color:var(--accent)">${orderId}</code><br><br>
      In a real app, the Razorpay checkout popup would open here. After payment,
      call <code>POST /payments/verify</code> with the callback data.
    </p>
    <div class="modal-actions">
      <button class="btn btn-success" onclick="closeModal();toast('Payment flow complete!','success')">Got it</button>
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
    toast('Course created!', 'success');
    ['cTitle','cDesc','cPrice','cDuration','cInstructor','cCategory'].forEach(id =>
      document.getElementById(id).value = '');
    showPage('courses');
  } catch(e) { toast(e.message, 'error'); }
}

async function deleteCourse(id) {
  if (!confirm('Delete this course?')) return;
  try {
    await DEL(`/courses/${id}`);
    toast('Course deleted', 'success');
    closeModal();
    loadCourses();
  } catch(e) { toast(e.message, 'error'); }
}

// ═══════════════════════════════════════════════════
// EVENTS
// ═══════════════════════════════════════════════════
async function loadEvents() {
  document.getElementById('eventsGrid').innerHTML = loadingHTML();
  try {
    const data = await GET('/events');
    allEvents = data.events;
    renderEventCards(allEvents, 'eventsGrid');
  } catch(e) { toast('Failed to load events', 'error'); }
}

function filterEvents(type, tabEl) {
  document.querySelectorAll('.filter-tabs .tab').forEach(t => t.classList.remove('active'));
  tabEl.classList.add('active');
  const filtered = type === 'all' ? allEvents : allEvents.filter(e => e.event_type === type);
  renderEventCards(filtered, 'eventsGrid');
}

function renderEventCards(events, gridId) {
  const grid = document.getElementById(gridId);
  if (!events.length) { grid.innerHTML = emptyHTML('No events found'); return; }
  grid.innerHTML = events.map(e => {
    const isFree = e.price === 0;
    const badgeClass = e.event_type === 'workshop' ? 'badge-workshop' : 'badge-event';
    const date = new Date(e.event_date).toLocaleDateString('en-IN', { day:'numeric', month:'short', year:'numeric' });
    return `
    <div class="card">
      <span class="card-type-badge ${badgeClass}">${e.event_type}</span>
      <span class="card-type-badge ${isFree ? 'badge-free' : 'badge-paid'}" style="margin-left:6px">${isFree ? 'FREE' : '₹'+e.price}</span>
      <h3>${esc(e.title)}</h3>
      <p>${esc(e.description)}</p>
      <div class="card-meta">
        <span class="meta-item">📅 ${date}</span>
        ${e.venue ? `<span class="meta-item">📍 ${esc(e.venue)}</span>` : ''}
        <span class="meta-item">👥 ${e.registered_count}/${e.capacity}</span>
      </div>
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
    const e = data.event;
    const date = new Date(e.event_date).toLocaleString('en-IN');
    openModal(`
      <h2>${esc(e.title)}</h2>
      <span class="card-type-badge ${e.event_type==='workshop'?'badge-workshop':'badge-event'}">${e.event_type}</span>
      <div class="modal-detail" style="margin-top:1rem">
        <div class="modal-detail-row"><span>Date</span><span>${date}</span></div>
        <div class="modal-detail-row"><span>Venue</span><span>${esc(e.venue||'–')}</span></div>
        <div class="modal-detail-row"><span>Price</span><span>${e.price===0 ? 'FREE' : '₹'+e.price}</span></div>
        <div class="modal-detail-row"><span>Capacity</span><span>${e.registered_count}/${e.capacity} registered</span></div>
      </div>
      <p style="color:var(--text2);line-height:1.7;margin:1rem 0">${esc(e.description)}</p>
      <div class="modal-actions">
        <button class="btn btn-primary" onclick="registerEvent(${e.id},'${esc(e.title)}',${e.price});closeModal()">Register</button>
        ${canManageEvent(e) ? `
          <button class="btn btn-danger" onclick="deleteEvent(${e.id})">Delete</button>
        ` : ''}
      </div>
    `);
  } catch(e) { toast(e.message, 'error'); }
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
      toast(`Registered for "${title}"!`, 'success');
    }
  } catch(e) { toast(e.message, 'error'); }
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
    toast('Event created!', 'success');
    showPage('events');
  } catch(e) { toast(e.message, 'error'); }
}

async function deleteEvent(id) {
  if (!confirm('Delete this event?')) return;
  try {
    await DEL(`/events/${id}`);
    toast('Event deleted', 'success');
    closeModal(); loadEvents();
  } catch(e) { toast(e.message, 'error'); }
}

// ═══════════════════════════════════════════════════
// ANNOUNCEMENTS
// ═══════════════════════════════════════════════════
async function loadAnnouncements() {
  document.getElementById('announcementsList').innerHTML = loadingHTML();
  try {
    const data = await GET('/announcements');
    const list = document.getElementById('announcementsList');
    if (!data.announcements.length) { list.innerHTML = emptyHTML('No announcements yet'); return; }
    list.innerHTML = data.announcements.map(a => `
      <div class="list-item">
        <div class="list-item-header">
          <h3>${esc(a.title)}</h3>
          <span class="meta-item" style="font-size:0.78rem;color:var(--text3)">${timeAgo(a.created_at)}</span>
        </div>
        <p>${esc(a.content)}</p>
      </div>`).join('');
  } catch(e) { toast('Failed to load announcements', 'error'); }
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
    document.getElementById('annTitle').value = '';
    document.getElementById('annContent').value = '';
    showPage('announcements');
  } catch(e) { toast(e.message, 'error'); }
}

// ═══════════════════════════════════════════════════
// FEEDBACK
// ═══════════════════════════════════════════════════
async function loadFeedback() {
  document.getElementById('feedbackList').innerHTML = loadingHTML();
  try {
    const data = await GET('/feedback');
    const list = document.getElementById('feedbackList');
    if (!data.feedback.length) { list.innerHTML = emptyHTML('No feedback yet'); return; }
    list.innerHTML = data.feedback.map(f => `
      <div class="list-item">
        <div class="list-item-header">
          <h3>${'★'.repeat(f.rating)}${'☆'.repeat(5-f.rating)} &nbsp;
            <small style="color:var(--text3);font-weight:400">${f.feedback_type} #${f.course_id||f.event_id}</small>
          </h3>
          <span class="card-type-badge ${f.feedback_type==='course'?'badge-course':'badge-event'}">${f.feedback_type}</span>
        </div>
        ${f.comment ? `<p>${esc(f.comment)}</p>` : ''}
        <div class="list-item-meta">
          <span>User #${f.user_id}</span>
          <span>${timeAgo(f.created_at)}</span>
        </div>
      </div>`).join('');
  } catch(e) { toast('Failed to load feedback', 'error'); }
}

async function initFeedbackForm() {
  if (!requireLogin()) return;
  await loadFeedbackItems();
}

async function loadFeedbackItems() {
  const type = document.getElementById('fbType').value;
  const sel  = document.getElementById('fbItem');
  try {
    if (type === 'course') {
      const data = await GET('/courses');
      sel.innerHTML = data.courses.map(c => `<option value="${c.id}">${esc(c.title)}</option>`).join('');
    } else {
      const data = await GET('/events');
      sel.innerHTML = data.events.map(e => `<option value="${e.id}">${esc(e.title)}</option>`).join('');
    }
  } catch(e) { toast('Failed to load items', 'error'); }
}

function setRating(n) {
  currentRating = n;
  document.getElementById('fbRating').value = n;
  document.querySelectorAll('#starRating span').forEach((s, i) => {
    s.classList.toggle('lit', i < n);
  });
}

async function submitFeedback() {
  if (!requireLogin()) return;
  const body = {
    feedback_type: document.getElementById('fbType').value,
    item_id:       parseInt(document.getElementById('fbItem').value),
    rating:        currentRating,
    comment:       document.getElementById('fbComment').value.trim(),
  };
  if (!body.rating) return toast('Please select a rating', 'error');
  try {
    await POST('/feedback', body);
    toast('Feedback submitted!', 'success');
    showPage('feedback-page');
  } catch(e) { toast(e.message, 'error'); }
}

// ═══════════════════════════════════════════════════
// MY REGISTRATIONS
// ═══════════════════════════════════════════════════
async function loadMyRegistrations() {
  if (!requireLogin()) return;
  document.getElementById('myRegistrationsList').innerHTML = loadingHTML();
  try {
    const data = await GET('/events/my-registrations');
    const list = document.getElementById('myRegistrationsList');
    if (!data.registrations.length) { list.innerHTML = emptyHTML('No registrations yet'); return; }
    list.innerHTML = data.registrations.map(r => `
      <div class="list-item">
        <div class="list-item-header">
          <h3>${esc(r.event_title || 'Event #'+r.event_id)}</h3>
          <span class="status-pill status-${r.status}">${r.status}</span>
        </div>
        <div class="list-item-meta">
          <span>Registration #${r.id}</span>
          <span>${timeAgo(r.registered_at)}</span>
        </div>
      </div>`).join('');
  } catch(e) { toast(e.message, 'error'); }
}

// ═══════════════════════════════════════════════════
// PAYMENT HISTORY
// ═══════════════════════════════════════════════════
async function loadPaymentHistory() {
  if (!requireLogin()) return;
  document.getElementById('paymentHistoryList').innerHTML = loadingHTML();
  try {
    const data = await GET('/payments/history');
    const list = document.getElementById('paymentHistoryList');
    if (!data.payments.length) { list.innerHTML = emptyHTML('No payments yet'); return; }
    list.innerHTML = data.payments.map(p => `
      <div class="list-item">
        <div class="list-item-header">
          <h3>₹${p.amount.toLocaleString()} — ${p.payment_type} payment</h3>
          <span class="status-pill status-${p.status}">${p.status}</span>
        </div>
        <div class="list-item-meta">
          <span>Order: ${p.razorpay_order_id}</span>
          <span>${timeAgo(p.created_at)}</span>
        </div>
      </div>`).join('');
  } catch(e) { toast(e.message, 'error'); }
}

// ═══════════════════════════════════════════════════
// ADMIN DASHBOARD
// ═══════════════════════════════════════════════════
async function loadAdminTab(tab, tabEl) {
  // update tab styling
  document.querySelectorAll('.admin-tabs .tab').forEach(t => t.classList.remove('active'));
  if (tabEl) tabEl.classList.add('active');
  else {
    const tabs = document.querySelectorAll('.admin-tabs .tab');
    if (tabs.length) tabs[0].classList.add('active');
  }

  const content = document.getElementById('adminContent');
  content.innerHTML = loadingHTML();

  try {
    if (tab === 'users') {
      const data = await GET('/admin/users');
      content.innerHTML = `
        <div class="admin-table-wrap">
        <table>
          <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Role</th><th>Active</th><th>Actions</th></tr></thead>
          <tbody>${data.users.map(u => `
            <tr>
              <td>#${u.id}</td>
              <td>${esc(u.name)}</td>
              <td>${esc(u.email)}</td>
              <td><span class="status-pill status-confirmed">${u.role}</span></td>
              <td>${u.is_active ? '✅' : '❌'}</td>
              <td><div class="admin-actions">
                <button class="btn btn-sm btn-ghost" onclick="adminToggleUser(${u.id},${!u.is_active})">${u.is_active?'Deactivate':'Activate'}</button>
                <button class="btn btn-sm btn-danger" onclick="adminDeleteUser(${u.id})">Delete</button>
              </div></td>
            </tr>`).join('')}
          </tbody>
        </table></div>`;

    } else if (tab === 'courses') {
      const data = await GET('/admin/courses');
      content.innerHTML = `
        <div class="admin-table-wrap">
        <table>
          <thead><tr><th>ID</th><th>Title</th><th>Category</th><th>Price</th><th>Actions</th></tr></thead>
          <tbody>${data.courses.map(c => `
            <tr>
              <td>#${c.id}</td>
              <td>${esc(c.title)}</td>
              <td>${esc(c.category||'–')}</td>
              <td>₹${c.price}</td>
              <td><button class="btn btn-sm btn-danger" onclick="adminDeleteCourse(${c.id})">Delete</button></td>
            </tr>`).join('')}
          </tbody>
        </table></div>`;

    } else if (tab === 'events') {
      const data = await GET('/admin/events');
      content.innerHTML = `
        <div class="admin-table-wrap">
        <table>
          <thead><tr><th>ID</th><th>Title</th><th>Type</th><th>Date</th><th>Price</th><th>Actions</th></tr></thead>
          <tbody>${data.events.map(e => `
            <tr>
              <td>#${e.id}</td>
              <td>${esc(e.title)}</td>
              <td>${e.event_type}</td>
              <td>${new Date(e.event_date).toLocaleDateString('en-IN')}</td>
              <td>${e.price===0?'FREE':'₹'+e.price}</td>
              <td><button class="btn btn-sm btn-danger" onclick="adminDeleteEvent(${e.id})">Delete</button></td>
            </tr>`).join('')}
          </tbody>
        </table></div>`;

    } else if (tab === 'payments') {
      const data = await GET('/admin/payments');
      const paid = data.payments.filter(p => p.status === 'paid');
      content.innerHTML = `
        <div class="stats-row">
          <div class="stat-card"><div class="num">${data.payments.length}</div><div class="lbl">Total Orders</div></div>
          <div class="stat-card"><div class="num">${paid.length}</div><div class="lbl">Paid</div></div>
          <div class="stat-card"><div class="num">₹${(data.total_revenue||0).toLocaleString()}</div><div class="lbl">Revenue</div></div>
        </div>
        <div class="admin-table-wrap">
        <table>
          <thead><tr><th>ID</th><th>User</th><th>Type</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead>
          <tbody>${data.payments.map(p => `
            <tr>
              <td>#${p.id}</td>
              <td>#${p.user_id}</td>
              <td>${p.payment_type}</td>
              <td>₹${p.amount}</td>
              <td><span class="status-pill status-${p.status}">${p.status}</span></td>
              <td>${timeAgo(p.created_at)}</td>
            </tr>`).join('')}
          </tbody>
        </table></div>`;
    }
  } catch(e) { content.innerHTML = `<p style="color:var(--danger);padding:2rem">${e.message}</p>`; }
}

async function adminToggleUser(id, active) {
  try {
    await PUT(`/admin/users/${id}`, { is_active: active });
    toast(`User ${active ? 'activated' : 'deactivated'}`, 'success');
    loadAdminTab('users', null);
  } catch(e) { toast(e.message, 'error'); }
}

async function adminDeleteUser(id) {
  if (!confirm('Delete this user permanently?')) return;
  try {
    await DEL(`/admin/users/${id}`);
    toast('User deleted', 'success');
    loadAdminTab('users', null);
  } catch(e) { toast(e.message, 'error'); }
}

async function adminDeleteCourse(id) {
  if (!confirm('Delete this course?')) return;
  try {
    await DEL(`/admin/courses/${id}`);
    toast('Course deleted', 'success');
    loadAdminTab('courses', null);
  } catch(e) { toast(e.message, 'error'); }
}

async function adminDeleteEvent(id) {
  if (!confirm('Delete this event?')) return;
  try {
    await DEL(`/admin/events/${id}`);
    toast('Event deleted', 'success');
    loadAdminTab('events', null);
  } catch(e) { toast(e.message, 'error'); }
}

// ═══════════════════════════════════════════════════
// MODAL
// ═══════════════════════════════════════════════════
function openModal(html) {
  document.getElementById('modalContent').innerHTML = html;
  document.getElementById('modalOverlay').classList.remove('hidden');
}
function closeModal() {
  document.getElementById('modalOverlay').classList.add('hidden');
}

// ═══════════════════════════════════════════════════
// DROPDOWN
// ═══════════════════════════════════════════════════
function toggleDropdown() {
  document.getElementById('dropdownMenu').classList.toggle('open');
}
function closeDropdown() {
  document.getElementById('dropdownMenu').classList.remove('open');
}
document.addEventListener('click', e => {
  if (!e.target.closest('.dropdown')) closeDropdown();
});

// ═══════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════
function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function loadingHTML() {
  return `<div class="loading"><div class="spinner"></div> Loading…</div>`;
}

function emptyHTML(msg) {
  return `<div class="empty-state"><div class="icon">📭</div><p>${msg}</p></div>`;
}

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  if (mins < 1)  return 'just now';
  if (mins < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

// ═══════════════════════════════════════════════════
// BOOT
// ═══════════════════════════════════════════════════
updateNavForUser();
showPage('home');