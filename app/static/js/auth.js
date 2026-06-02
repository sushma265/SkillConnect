/**
 * SkillConnect – Auth JavaScript
 * =================================
 * Authentication-related functions loaded on all pages.
 * Works with the main.js auth state management.
 */

// This file exists as a namespace for future auth-specific logic
// (e.g., password strength indicators, MFA). The core login/register
// handlers are inline in the respective templates for clarity.

/**
 * Check if the current user is authenticated.
 * @returns {boolean} True if a valid token exists.
 */
function isAuthenticated() {
    return !!localStorage.getItem('sc_token');
}

/**
 * Get the current user object from localStorage.
 * @returns {object|null} User object or null.
 */
function getCurrentUser() {
    const raw = localStorage.getItem('sc_user');
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch (e) {
        return null;
    }
}

/**
 * Check if the user has a specific role.
 * @param {string} role - Role to check ('attendee', 'organizer', 'admin').
 * @returns {boolean} True if the user has the given role.
 */
function hasRole(role) {
    const user = getCurrentUser();
    return user ? user.role === role : false;
}

/**
 * Check if the user has organizer-level access (organizer or admin).
 * @returns {boolean}
 */
function isOrganizer() {
    const user = getCurrentUser();
    return user ? ['organizer', 'admin'].includes(user.role) : false;
}

/**
 * Check if the user has admin access.
 * @returns {boolean}
 */
function isAdmin() {
    return hasRole('admin');
}

/**
 * Require authentication – redirect to login if not authenticated.
 * Call this at the top of pages that require login.
 */
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

/**
 * Require a specific role – redirect to dashboard if unauthorized.
 * @param  {...string} roles - Allowed roles.
 */
function requireRole(...roles) {
    if (!requireAuth()) return false;
    const user = getCurrentUser();
    if (!user || !roles.includes(user.role)) {
        showToast('Access denied', 'danger');
        window.location.href = '/dashboard';
        return false;
    }
    return true;
}
