/* MJ Developer Platform — Main JavaScript */

'use strict';

// Auto-dismiss flash alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.alert.alert-dismissible');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // Animate cards on page load
  const cards = document.querySelectorAll('.card');
  cards.forEach(function (card, i) {
    card.style.animationDelay = (i * 0.04) + 's';
    card.classList.add('fade-in');
  });

  // Active nav link highlight
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(function (link) {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // Confirm delete forms
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  // Color picker live preview
  const colorPickers = document.querySelectorAll('input[type="color"]');
  colorPickers.forEach(function (picker) {
    picker.addEventListener('input', function () {
      const textInput = picker.nextElementSibling;
      if (textInput && textInput.tagName === 'INPUT') {
        textInput.value = picker.value;
      }
    });
  });

  // UID search enter key support
  const uidInputs = document.querySelectorAll('input[name="uid"], input[name="guild_id"]');
  uidInputs.forEach(function (input) {
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        const form = input.closest('form');
        if (form) form.submit();
      }
    });
  });

  // Tooltips
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipTriggerList.forEach(function (el) {
    new bootstrap.Tooltip(el);
  });

  // Popovers
  const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
  popoverTriggerList.forEach(function (el) {
    new bootstrap.Popover(el);
  });
});

// Copy to clipboard helper
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(function () {
    showToast('Copied to clipboard!', 'success');
  });
}

// Simple toast helper
function showToast(message, type) {
  type = type || 'info';
  const toast = document.createElement('div');
  toast.className = 'toast align-items-center text-bg-' + type + ' border-0 position-fixed bottom-0 end-0 m-3';
  toast.setAttribute('role', 'alert');
  toast.innerHTML = '<div class="d-flex"><div class="toast-body">' + message + '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
  document.body.appendChild(toast);
  const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
  bsToast.show();
  toast.addEventListener('hidden.bs.toast', function () { toast.remove(); });
}

