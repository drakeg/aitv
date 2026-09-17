document.addEventListener('DOMContentLoaded', () => {
  const settings = document.querySelector('[data-discovery-settings]');
  const discoveryRegion = settings?.dataset.region || 'US';
  const requireRegionalAvailability = settings?.dataset.requireRegion === '1';
  const isAuthenticated = settings?.dataset.authenticated === '1';
  const importUrl = settings?.dataset.importUrl || '';
  const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';

  const updateRowEmptyState = (row) => {
    if (!row) return;
    const remainingCards = row.querySelectorAll('.card:not(.region-pending)');
    const pendingCards = row.querySelectorAll('.card.region-pending');
    const emptyState = row.querySelector('[data-region-empty-state]');
    if (!emptyState) return;
    emptyState.classList.toggle('d-none', Boolean(remainingCards.length || pendingCards.length));
  };

  const watchActionLabel = (data) => {
    const bestAccess = data.providers?.[0]?.access || '';
    if (bestAccess === 'Free') return 'Watch free options';
    if (bestAccess === 'Free with ads') return 'Watch free with ads';
    if (bestAccess === 'Subscription') return 'See subscription options';
    if (bestAccess === 'Rent') return 'See rental options';
    if (bestAccess === 'Buy') return 'See purchase options';
    return 'See regional watch options';
  };

  const enrichTmdbContext = async (element) => {
    if (element.dataset.contextLoaded === '1') return;
    element.dataset.contextLoaded = '1';
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
      if (requireRegion && !data.is_available_in_region) { card?.remove(); updateRowEmptyState(row); return; }
      card?.classList.remove('region-pending');
      updateRowEmptyState(row);
      const meta = [];
      if (contentType === 'tv') { meta.push(data.network || 'Network not listed'); meta.push(data.episode_label || 'Episode not listed'); }
      meta.push(data.runtime ? `${data.runtime} min` : 'Runtime not listed');
      summary.textContent = meta.join(' · ');
      providers.replaceChildren();
      renderProviders(providers, data);
      if (data.watch_url) { watch.href = data.watch_url; watch.textContent = watchActionLabel(data); watch.classList.remove('d-none'); }
    } catch (_error) {
      if (requireRegion) { card?.remove(); updateRowEmptyState(row); return; }
      card?.classList.remove('region-pending');
      updateRowEmptyState(row);
      summary.textContent = contentType === 'tv' ? 'Network unavailable · Episode unavailable · Runtime unavailable' : 'Runtime unavailable';
      providers.replaceChildren();
      addMutedPill(providers, 'Watch details temporarily unavailable');
    }
  };

  observeNearViewport(Array.from(document.querySelectorAll('[data-tmdb-context]')), enrichTmdbContext);
  const tvmazeCards = Array.from(document.querySelectorAll('.card[data-source-type="tvmaze"]'));

  const enrichTvmazeCard = async (card) => {
    if (card.dataset.tvmazeEnriched === '1') return;
    card.dataset.tvmazeEnriched = '1';
    const title = card.querySelector('.content-title')?.getAttribute('title')?.trim();
    const metadataOnly = card.dataset.hasDirectWatch === '0';
    const providerBox = card.querySelector('.provider-options');
    const detailsLink = card.querySelector('a.source-details-link[href*="tvmaze.com"]');
    const row = card.closest('[data-discovery-row]');
    if (!title || !detailsLink) { if (requireRegionalAvailability && metadataOnly) { card.remove(); updateRowEmptyState(row); } return; }
    const params = new URLSearchParams({title, region: discoveryRegion});
    if (card.dataset.releaseYear) params.set('year', card.dataset.releaseYear);
    try {
      const response = await fetch(`/content/tvmaze/watch-options/?${params.toString()}`, {headers: {'X-Requested-With': 'XMLHttpRequest'}, credentials: 'same-origin'});
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (!data.matched) { if (requireRegionalAvailability && metadataOnly) { card.remove(); updateRowEmptyState(row); } else card.classList.remove('region-pending'); return; }
      if (metadataOnly && !data.is_available_in_region && requireRegionalAvailability) { card.remove(); updateRowEmptyState(row); return; }
      if (metadataOnly && data.is_available_in_region && providerBox) {
        providerBox.replaceChildren();
        renderProviders(providerBox, data);
        if (data.watch_url && !card.querySelector('[data-tvmaze-regional-watch]')) {
          const action = document.createElement('a');
          action.className = 'btn btn-sm btn-primary w-100 mt-1'; action.target = '_blank'; action.rel = 'noopener noreferrer';
          action.href = data.watch_url; action.textContent = watchActionLabel(data); action.dataset.tvmazeRegionalWatch = '';
          detailsLink.before(action);
        }
      }
      if (data.tmdb_details_url && !card.querySelector('[data-tvmaze-tmdb-match]')) {
        const tmdb = document.createElement('a');
        tmdb.className = 'source-details-link'; tmdb.target = '_blank'; tmdb.rel = 'noopener noreferrer'; tmdb.href = data.tmdb_details_url;
        tmdb.textContent = 'TMDB match'; tmdb.dataset.tvmazeTmdbMatch = ''; detailsLink.after(tmdb);
      }
      renderTvmazeSaveControls(card, data);
      card.classList.remove('region-pending');
      if (data.favorite) window.aitvReorderFavoriteRow?.(row);
      updateRowEmptyState(row);
    } catch (_error) {
      if (requireRegionalAvailability && metadataOnly) { card.remove(); updateRowEmptyState(row); } else card.classList.remove('region-pending');
    }
  };

  observeNearViewport(tvmazeCards, enrichTvmazeCard);

  function renderTvmazeSaveControls(card, data) {
    if (!isAuthenticated || !importUrl || !data.tmdb_id || !data.tmdb_details_url || card.querySelector('[data-tvmaze-watchlist-control]')) return;
    const container = card.querySelector('.p-2'); if (!container) return;
    const form = document.createElement('form'); form.method = 'post'; form.dataset.watchlistForm = ''; form.dataset.tvmazeWatchlistControl = '';
    if (data.saved && data.remove_url) {
      form.action = data.remove_url; form.dataset.contentId = data.content_id || ''; appendCsrf(form);
      form.appendChild(makeButton('✓ Saved to Watchlist', 'btn-danger')); container.appendChild(form);
      if (data.favorite_url) {
        const favorite = document.createElement('form'); favorite.method = 'post'; favorite.action = data.favorite_url; favorite.dataset.favoriteForm = '';
        favorite.dataset.favoriteState = data.favorite ? '1' : '0'; appendCsrf(favorite); appendHidden(favorite, 'favorite', data.favorite ? '0' : '1');
        favorite.appendChild(makeButton(data.favorite ? '★ Favorite' : '☆ Mark favorite', data.favorite ? 'btn-warning' : 'btn-outline-light')); container.appendChild(favorite);
      }
      return;
    }
    form.action = importUrl; form.dataset.externalSave = 'true'; appendCsrf(form);
    appendHidden(form, 'title', data.tmdb_title || card.querySelector('.content-title')?.getAttribute('title') || 'TV Show');
    appendHidden(form, 'url', data.tmdb_details_url); appendHidden(form, 'genre', card.querySelector('.source-genre')?.getAttribute('title') || 'TV');
    appendHidden(form, 'thumbnail', card.querySelector('img')?.src || ''); appendHidden(form, 'content_type', 'tv'); appendHidden(form, 'description', '');
    appendHidden(form, 'release_year', card.dataset.releaseYear || ''); appendHidden(form, 'rating', ''); appendHidden(form, 'external_source', 'tmdb'); appendHidden(form, 'external_id', data.tmdb_id);
    form.appendChild(makeButton('⭐ Save to Watchlist', 'btn-success')); container.appendChild(form);
  }

  function appendCsrf(form) { if (csrfToken) appendHidden(form, 'csrfmiddlewaretoken', csrfToken); }
  function appendHidden(form, name, value) { const input = document.createElement('input'); input.type = 'hidden'; input.name = name; input.value = value || ''; form.appendChild(input); }
  function makeButton(label, className) { const button = document.createElement('button'); button.type = 'submit'; button.className = `btn btn-sm ${className} w-100 mt-1`; button.textContent = label; return button; }

  function observeNearViewport(elements, callback) {
    if (!elements.length) return;
    if (!('IntersectionObserver' in window)) { elements.forEach(callback); return; }
    const observer = new IntersectionObserver((entries) => entries.forEach((entry) => { if (!entry.isIntersecting) return; observer.unobserve(entry.target); callback(entry.target); }), {rootMargin: '500px'});
    elements.forEach((element) => observer.observe(element));
  }

  function renderProviderPill(container, provider, hidden = false) {
    const pill = document.createElement('span');
    pill.className = `provider-pill${hidden ? ' d-none' : ''}`;
    pill.textContent = `${provider.name} · ${provider.access}`;
    if (hidden) pill.dataset.additionalProvider = '';
    container.appendChild(pill);
  }

  function renderProviders(container, data) {
    const rows = data.providers || [];
    rows.forEach((provider) => renderProviderPill(container, provider));
    const allRows = data.all_providers || rows;
    const additionalRows = allRows.slice(rows.length);
    additionalRows.forEach((provider) => renderProviderPill(container, provider, true));
    if (additionalRows.length) {
      const more = document.createElement('button');
      more.type = 'button'; more.className = 'provider-pill provider-pill-more';
      more.textContent = `+${additionalRows.length} more`; more.setAttribute('aria-expanded', 'false');
      more.addEventListener('click', () => {
        const expanded = more.getAttribute('aria-expanded') === 'true';
        container.querySelectorAll('[data-additional-provider]').forEach((pill) => pill.classList.toggle('d-none', expanded));
        more.setAttribute('aria-expanded', expanded ? 'false' : 'true');
        more.textContent = expanded ? `+${additionalRows.length} more` : 'Show fewer';
      });
      container.appendChild(more);
    } else if (!rows.length) addMutedPill(container, `No ${data.region || 'regional'} providers listed`);
  }

  function addMutedPill(container, text) { const unavailable = document.createElement('span'); unavailable.className = 'provider-pill provider-pill-muted'; unavailable.textContent = text; container.appendChild(unavailable); }
});
