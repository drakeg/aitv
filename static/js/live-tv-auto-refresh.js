(() => {
  const REFRESH_INTERVAL_MS = 60_000;
  const STORAGE_KEY = 'aitvLiveTvAutoRefreshPaused';
  const toggles = Array.from(
    document.querySelectorAll('[data-live-tv-refresh-toggle]'),
  );
  let pausedFallback = false;

  const readPaused = () => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored !== null) {
        pausedFallback = stored === '1';
      }
    } catch (_error) {
      // Keep the in-memory state when browser storage is unavailable.
    }
    return pausedFallback;
  };

  const writePaused = (paused) => {
    pausedFallback = paused;
    try {
      window.localStorage.setItem(STORAGE_KEY, paused ? '1' : '0');
    } catch (_error) {
      // The control still works for this page through pausedFallback.
    }
  };

  const renderToggles = () => {
    const paused = readPaused();
    toggles.forEach((toggle) => {
      toggle.setAttribute('aria-pressed', paused ? 'true' : 'false');
      toggle.textContent = paused ? 'Resume auto-refresh' : 'Pause auto-refresh';
    });
  };

  toggles.forEach((toggle) => {
    toggle.addEventListener('click', () => {
      writePaused(!readPaused());
      renderToggles();
    });
  });

  window.addEventListener('storage', (event) => {
    if (event.key === STORAGE_KEY) {
      renderToggles();
    }
  });

  renderToggles();

  window.setInterval(() => {
    if (readPaused() || document.visibilityState !== 'visible') {
      return;
    }

    const active = document.activeElement;
    if (
      active
      && active !== document.body
      && active !== document.documentElement
    ) {
      return;
    }

    window.location.reload();
  }, REFRESH_INTERVAL_MS);
})();
