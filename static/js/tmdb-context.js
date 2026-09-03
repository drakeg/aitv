document.addEventListener('DOMContentLoaded', () => {
  const contexts = document.querySelectorAll('[data-tmdb-context]');

  contexts.forEach(async (element) => {
    const url = element.dataset.contextUrl;
    const summary = element.querySelector('[data-context-summary]');
    const providers = element.querySelector('[data-context-providers]');
    const watch = element.querySelector('[data-context-watch]');

    if (!url) return;

    try {
      const response = await fetch(url, {
        headers: {'X-Requested-With': 'XMLHttpRequest'},
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      const meta = [];
      if (data.network) meta.push(data.network);
      if (data.episode_label) meta.push(data.episode_label);
      if (data.runtime) meta.push(`${data.runtime} min`);
      summary.textContent = meta.length ? meta.join(' · ') : 'Watch availability';

      providers.replaceChildren();
      (data.providers || []).forEach((provider) => {
        const pill = document.createElement('span');
        pill.className = 'provider-pill';
        pill.textContent = `${provider.name} · ${provider.access}`;
        providers.appendChild(pill);
      });

      if (data.watch_url) {
        watch.href = data.watch_url;
        watch.classList.remove('d-none');
      }

      if (!(data.providers || []).length && !data.network && !data.runtime) {
        summary.textContent = 'No US watch details found yet.';
      }
    } catch (_error) {
      summary.textContent = 'Watch details temporarily unavailable.';
    }
  });
});
