document.addEventListener('DOMContentLoaded', () => {
  const settings = document.querySelector('[data-discovery-settings]');
  const discoveryRegion = settings?.dataset.region || 'US';
  const requireRegionalAvailability = settings?.dataset.requireRegion === '1';

  const updateRowEmptyState = (row) => {
    if (!row) return;
    const remainingCards = row.querySelectorAll('.card:not(.region-pending)');
    const pendingCards = row.querySelectorAll('.card.region-pending');
    const emptyState = row.querySelector('[data-region-empty-state]');
    if (!emptyState) return;
    emptyState.classList.toggle('d-none', Boolean(remainingCards.length || pendingCards.length));
  };

  document.querySelectorAll('[data-tmdb-context]').forEach(async (element) => {
    const url = element.dataset.contextUrl;
    const summary = element.querySelector('[data-context-summary]');
    const providers = element.querySelector('[data-context-providers]');
    const watch = element.querySelector('[data-context-watch]');
    const contentType = element.dataset.contentType;
    const requireRegion = element.dataset.requireRegion === '1';
    const card = element.closest('.card');
    const row = element.closest('[data-discovery-row]');
    if (!url) return;

    try {
      const response = await fetch(url, {headers: {'X-Requested-With': 'XMLHttpRequest'}});
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (requireRegion && !data.is_available_in_region) {
        card?.remove();
        updateRowEmptyState(row);
        return;
      }
      card?.classList.remove('region-pending');
      updateRowEmptyState(row);

      const meta = [];
      if (contentType === 'tv') {
        meta.push(data.network || 'Network not listed');
        meta.push(data.episode_label || 'Episode not listed');
      }
      meta.push(data.runtime ? `${data.runtime} min` : 'Runtime not listed');
      summary.textContent = meta.join(' · ');
      providers.replaceChildren();
      renderProviders(providers, data);
      if (data.watch_url) {
        watch.href = data.watch_url;
        watch.classList.remove('d-none');
      }
    } catch (_error) {
      if (requireRegion) {
        card?.remove();
        updateRowEmptyState(row);
        return;
      }
      card?.classList.remove('region-pending');
      updateRowEmptyState(row);
      summary.textContent = contentType === 'tv'
        ? 'Network unavailable · Episode unavailable · Runtime unavailable'
        : 'Runtime unavailable';
      providers.replaceChildren();
      addMutedPill(providers, 'Watch details temporarily unavailable');
    }
  });

  const metadataOnlyTvmazeCards = Array.from(
    document.querySelectorAll('.card[data-source-type="tvmaze"][data-has-direct-watch="0"]'),
  );

  const enrichTvmazeCard = async (card) => {
    if (card.dataset.tvmazeEnriched === '1') return;
    card.dataset.tvmazeEnriched = '1';
    const title = card.querySelector('.content-title')?.getAttribute('title')?.trim();
    const providerBox = card.querySelector('.provider-options');
    const detailsLink = card.querySelector('a.source-details-link[href*="tvmaze.com"]');
    const row = card.closest('[data-discovery-row]');
    if (!title || !providerBox || !detailsLink) {
      if (requireRegionalAvailability) {
        card.remove();
        updateRowEmptyState(row);
      }
      return;
    }

    const params = new URLSearchParams({title, region: discoveryRegion});
    if (card.dataset.releaseYear) params.set('year', card.dataset.releaseYear);

    try {
      const response = await fetch(`/content/tvmaze/watch-options/?${params.toString()}`, {
        headers: {'X-Requested-With': 'XMLHttpRequest'},
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (!data.matched || !data.is_available_in_region) {
        if (requireRegionalAvailability) {
          card.remove();
          updateRowEmptyState(row);
        } else {
          card.classList.remove('region-pending');
        }
        return;
      }

      providerBox.replaceChildren();
      renderProviders(providerBox, data);
      if (data.watch_url) {
        const action = document.createElement('a');
        action.className = 'btn btn-sm btn-primary w-100 mt-1';
        action.target = '_blank';
        action.rel = 'noopener noreferrer';
        action.href = data.watch_url;
        action.textContent = 'See regional watch options';
        detailsLink.before(action);
      }
      if (data.tmdb_details_url) {
        const tmdb = document.createElement('a');
        tmdb.className = 'source-details-link';
        tmdb.target = '_blank';
        tmdb.rel = 'noopener noreferrer';
        tmdb.href = data.tmdb_details_url;
        tmdb.textContent = 'TMDB match';
        detailsLink.after(tmdb);
      }
      card.classList.remove('region-pending');
      updateRowEmptyState(row);
    } catch (_error) {
      if (requireRegionalAvailability) {
        card.remove();
        updateRowEmptyState(row);
      } else {
        card.classList.remove('region-pending');
      }
    }
  };

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        enrichTvmazeCard(entry.target);
      });
    }, {rootMargin: '300px'});
    metadataOnlyTvmazeCards.forEach((card) => observer.observe(card));
  } else {
    metadataOnlyTvmazeCards.forEach(enrichTvmazeCard);
  }

  function renderProviders(container, data) {
    const rows = data.providers || [];
    rows.forEach((provider) => {
      const pill = document.createElement('span');
      pill.className = 'provider-pill';
      pill.textContent = `${provider.name} · ${provider.access}`;
      container.appendChild(pill);
    });
    if (data.additional_provider_count) {
      const more = document.createElement('span');
      more.className = 'provider-pill provider-pill-more';
      more.textContent = `+${data.additional_provider_count} more`;
      container.appendChild(more);
    } else if (!rows.length) {
      addMutedPill(container, `No ${data.region || 'regional'} providers listed`);
    }
  }

  function addMutedPill(container, text) {
    const unavailable = document.createElement('span');
    unavailable.className = 'provider-pill provider-pill-muted';
    unavailable.textContent = text;
    container.appendChild(unavailable);
  }
});
