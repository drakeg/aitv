document.addEventListener('DOMContentLoaded', () => {
  const contexts = document.querySelectorAll('[data-tmdb-context]');

  contexts.forEach(async (element) => {
    const url = element.dataset.contextUrl;
    const summary = element.querySelector('[data-context-summary]');
    const providers = element.querySelector('[data-context-providers]');
    const watch = element.querySelector('[data-context-watch]');
    const contentType = element.dataset.contentType;
    const requireRegion = element.dataset.requireRegion === '1';
    const card = element.closest('.card');

    if (!url) return;

    try {
      const response = await fetch(url, {
        headers: {'X-Requested-With': 'XMLHttpRequest'},
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      if (requireRegion && !data.is_available_in_region) {
        card?.remove();
        return;
      }
      card?.classList.remove('region-pending');

      const meta = [];
      if (contentType === 'tv') {
        meta.push(data.network || 'Network not listed');
        meta.push(data.episode_label || 'Episode not listed');
      }
      meta.push(data.runtime ? `${data.runtime} min` : 'Runtime not listed');
      summary.textContent = meta.join(' · ');

      providers.replaceChildren();
      const rows = data.providers || [];
      rows.forEach((provider) => {
        const pill = document.createElement('span');
        pill.className = 'provider-pill';
        pill.textContent = `${provider.name} · ${provider.access}`;
        providers.appendChild(pill);
      });

      if (data.additional_provider_count) {
        const more = document.createElement('span');
        more.className = 'provider-pill provider-pill-more';
        more.textContent = `+${data.additional_provider_count} more`;
        providers.appendChild(more);
      } else if (!rows.length) {
        const unavailable = document.createElement('span');
        unavailable.className = 'provider-pill provider-pill-muted';
        unavailable.textContent = `No ${data.region || 'regional'} providers listed`;
        providers.appendChild(unavailable);
      }

      if (data.watch_url) {
        watch.href = data.watch_url;
        watch.classList.remove('d-none');
      }
    } catch (_error) {
      if (requireRegion) {
        card?.remove();
        return;
      }
      card?.classList.remove('region-pending');
      summary.textContent = contentType === 'tv'
        ? 'Network unavailable · Episode unavailable · Runtime unavailable'
        : 'Runtime unavailable';
      providers.replaceChildren();
      const unavailable = document.createElement('span');
      unavailable.className = 'provider-pill provider-pill-muted';
      unavailable.textContent = 'Watch details temporarily unavailable';
      providers.appendChild(unavailable);
    }
  });
});
