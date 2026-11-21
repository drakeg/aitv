(() => {
  const buttons = Array.from(document.querySelectorAll('[data-copy-target]'));
  const status = document.querySelector('[data-copy-status]');

  if (!buttons.length || !status) {
    return;
  }

  const announce = (message) => {
    status.textContent = '';
    window.requestAnimationFrame(() => {
      status.textContent = message;
    });
  };

  const fallbackCopy = (input) => {
    input.focus();
    input.select();
    input.setSelectionRange(0, input.value.length);
    const copied = document.execCommand('copy');
    input.blur();
    return copied;
  };

  buttons.forEach((button) => {
    button.addEventListener('click', async () => {
      const input = document.getElementById(button.dataset.copyTarget);
      if (!input) {
        announce('Unable to find the URL to copy.');
        return;
      }

      const label = button.dataset.copyLabel || 'URL';
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(input.value);
        } else if (!fallbackCopy(input)) {
          throw new Error('copy command was rejected');
        }

        const originalText = button.textContent;
        button.textContent = 'Copied';
        announce(`${label} copied to clipboard.`);
        window.setTimeout(() => {
          button.textContent = originalText;
        }, 1500);
      } catch (_error) {
        announce(`Could not copy ${label}. Select the URL and copy it manually.`);
        input.focus();
        input.select();
      }
    });
  });
})();
