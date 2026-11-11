(() => {
  const REFRESH_INTERVAL_MS = 60_000;

  window.setInterval(() => {
    if (document.visibilityState !== 'visible') {
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
