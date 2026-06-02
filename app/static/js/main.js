/**
 * SkillConnect – Main JavaScript
 * =================================
 * Core utilities: toast notifications, navbar state management,
 * Google OAuth token capture, and shared helpers.
 */

// ── Toast Notification System ──────────────────────────────────────────

/**
 * Display a Bootstrap toast notification.
 * @param {string} message - The notification message.
 * @param {string} type - Bootstrap color: 'success', 'danger', 'warning', 'info'.
 * @param {number} duration - Auto-hide delay in milliseconds.
 */
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const icons = {
        success: 'bi-check-circle-fill',
        danger: 'bi-exclamation-triangle-fill',
        warning: 'bi-exclamation-circle-fill',
        info: 'bi-info-circle-fill',
    };

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi ${icons[type] || icons.info} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    container.appendChild(toastEl);
    const bsToast = new bootstrap.Toast(toastEl, { delay: duration });
    bsToast.show();

    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}


// ── API Helper ─────────────────────────────────────────────────────────

/**
 * Make an authenticated API request.
 * @param {string} url - API endpoint URL.
 * @param {object} options - Fetch options (method, body, etc.).
 * @returns {Promise<object>} Parsed JSON response.
 */
async function apiFetch(url, options = {}) {
    const token = localStorage.getItem('sc_token');
    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...(options.headers || {}),
    };

    const response = await fetch(url, { ...options, headers });

    // Handle 401 - token expired
    if (response.status === 401) {
        const refreshed = await refreshToken();
        if (refreshed) {
            // Retry with new token
            headers['Authorization'] = `Bearer ${localStorage.getItem('sc_token')}`;
            return fetch(url, { ...options, headers }).then(r => r.json());
        } else {
            logout();
            throw new Error('Session expired');
        }
    }

    return response.json();
}


// ── Token Refresh ──────────────────────────────────────────────────────

/**
 * Attempt to refresh the access token using the refresh token.
 * @returns {Promise<boolean>} True if refresh was successful.
 */
async function refreshToken() {
    const refreshTok = localStorage.getItem('sc_refresh_token');
    if (!refreshTok) return false;

    try {
        const res = await fetch('/auth/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${refreshTok}`,
            },
        });

        if (res.ok) {
            const data = await res.json();
            localStorage.setItem('sc_token', data.access_token);
            return true;
        }
    } catch (e) {
        console.error('Token refresh failed:', e);
    }

    return false;
}


// ── Logout ─────────────────────────────────────────────────────────────

/**
 * Clear stored tokens and redirect to login.
 */
function logout() {
    localStorage.removeItem('sc_token');
    localStorage.removeItem('sc_refresh_token');
    localStorage.removeItem('sc_user');
    window.location.href = '/login';
}


// ── Navbar State Management ────────────────────────────────────────────

/**
 * Update the navbar to reflect login state.
 */
function updateNavbar() {
    const user = JSON.parse(localStorage.getItem('sc_user') || 'null');
    const authButtons = document.getElementById('authButtons');
    const userMenu = document.getElementById('userMenu');

    if (!authButtons || !userMenu) return;

    if (user && user.id) {
        authButtons.classList.add('d-none');
        userMenu.classList.remove('d-none');
        userMenu.classList.add('d-flex');

        // Set avatar and name
        const avatar = document.getElementById('navAvatar');
        const userName = document.getElementById('navUserName');
        const dropdownHeader = document.getElementById('dropdownHeader');

        if (avatar) avatar.textContent = (user.name || 'U')[0].toUpperCase();
        if (userName) userName.textContent = user.name || 'User';
        if (dropdownHeader) dropdownHeader.textContent = `${user.name} (${user.role})`;

        // Show role-specific menu items
        const organizerItems = document.getElementById('organizerMenuItems');
        const adminItems = document.getElementById('adminMenuItems');

        if (organizerItems && (user.role === 'organizer' || user.role === 'admin')) {
            organizerItems.classList.remove('d-none');
        }
        if (adminItems && user.role === 'admin') {
            adminItems.classList.remove('d-none');
        }
    } else {
        authButtons.classList.remove('d-none');
        userMenu.classList.add('d-none');
        userMenu.classList.remove('d-flex');
    }
}


// ── Google OAuth Token Capture ─────────────────────────────────────────

/**
 * Check URL params for OAuth callback token and store it.
 */
function captureOAuthToken() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('sc_token');
    const userId = params.get('sc_user_id');
    const authError = params.get('auth_error');

    if (authError) {
        showToast(`Authentication error: ${authError}`, 'danger');
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
    }

    if (token) {
        localStorage.setItem('sc_token', token);

        // Fetch user details
        fetch('/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` },
        })
        .then(res => res.json())
        .then(data => {
            if (data.user) {
                localStorage.setItem('sc_user', JSON.stringify(data.user));
                showToast('Logged in with Google!', 'success');
                updateNavbar();
                // Redirect to dashboard
                setTimeout(() => window.location.href = '/dashboard', 500);
            }
        })
        .catch(() => {
            showToast('Login successful', 'success');
        });

        // Clean URL params
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}


// ── Shared UI Helpers ──────────────────────────────────────────────────

/**
 * Open the Create Event modal.
 * If already on the dashboard page, opens the modal directly.
 * Otherwise, redirects to the dashboard with an action param.
 */
function showCreateEvent() {
    const modal = document.getElementById('createEventModal');
    if (modal) {
        // We're on the dashboard — open the modal directly
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    } else {
        // We're on another page — navigate to dashboard with action
        window.location.href = '/dashboard?action=create-event';
    }
}

/**
 * Navigate to profile section.
 */
function showProfile() {
    window.location.href = '/dashboard#profile';
}

/**
 * Format a date string for display.
 * @param {string} isoString - ISO 8601 date string.
 * @returns {string} Formatted date.
 */
function formatDate(isoString) {
    if (!isoString) return '–';
    return new Date(isoString).toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
    });
}

/**
 * Format a datetime string for display.
 * @param {string} isoString - ISO 8601 datetime string.
 * @returns {string} Formatted datetime.
 */
function formatDateTime(isoString) {
    if (!isoString) return '–';
    return new Date(isoString).toLocaleString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}


// ── Initialise on DOM Ready ────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    captureOAuthToken();
    updateNavbar();
});
