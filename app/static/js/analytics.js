/**
 * SkillConnect – Analytics JavaScript
 * ======================================
 * Shared analytics helpers and Chart.js configurations.
 */

// Shared chart theme for dark mode
const SC_CHART_DEFAULTS = {
    font: {
        family: "'Inter', sans-serif",
        color: '#94a3b8',
    },
    gridColor: 'rgba(148, 163, 184, 0.1)',
    colors: [
        'rgba(59, 130, 246, 0.7)',
        'rgba(99, 102, 241, 0.7)',
        'rgba(16, 185, 129, 0.7)',
        'rgba(245, 158, 11, 0.7)',
        'rgba(236, 72, 153, 0.7)',
        'rgba(6, 182, 212, 0.7)',
    ],
};

// Apply global Chart.js defaults if available
if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 16;
}

console.log('SkillConnect Analytics module loaded');
