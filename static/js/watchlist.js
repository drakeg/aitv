document.addEventListener('submit', async (event) => {
    const favoriteForm = event.target.closest('[data-favorite-form]');
    if (favoriteForm) {
        event.preventDefault();
        const button = favoriteForm.querySelector('button[type="submit"]');
        const input = favoriteForm.querySelector('input[name="favorite"]');
        if (!button || !input || button.disabled) return;

        const wasFavorite = favoriteForm.dataset.favoriteState === '1';
        const originalLabel = button.textContent;
        button.disabled = true;
        button.textContent = 'Updating…';

        try {
            const response = await fetch(favoriteForm.action, {
                method: 'POST',
                body: new FormData(favoriteForm),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                },
                credentials: 'same-origin',
            });
            if (!response.ok) throw new Error(`Favorite update failed: ${response.status}`);
            const result = await response.json();

            favoriteForm.dataset.favoriteState = result.favorite ? '1' : '0';
            input.value = result.favorite ? '0' : '1';
            button.textContent = result.favorite ? '★ Favorite' : '☆ Mark favorite';
            button.classList.toggle('btn-warning', result.favorite);
            button.classList.toggle('btn-outline-light', !result.favorite);

            const count = document.querySelector('[data-favorite-count]');
            if (count) {
                const current = Number.parseInt(count.textContent, 10) || 0;
                const next = Math.max(0, current + (result.favorite ? 1 : -1));
                count.textContent = `${next} favorite${next === 1 ? '' : 's'}.`;
            }
        } catch (error) {
            console.error(error);
            button.textContent = originalLabel;
            favoriteForm.dataset.favoriteState = wasFavorite ? '1' : '0';
            window.alert('Could not update the favorite. Please try again.');
        } finally {
            button.disabled = false;
        }
        return;
    }

    const form = event.target.closest('[data-watchlist-form]');
    if (!form) return;

    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    if (!button || button.disabled) return;

    const originalLabel = button.textContent;
    button.disabled = true;
    button.textContent = 'Saving…';

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
            },
            credentials: 'same-origin',
        });

        if (!response.ok) throw new Error(`Watchlist update failed: ${response.status}`);
        const result = await response.json();

        button.textContent = result.label;
        button.classList.toggle('btn-success', !result.saved);
        button.classList.toggle('btn-danger', result.saved);
        button.title = result.saved ? 'Remove from watchlist' : 'Save to watchlist';

        if (result.saved && result.remove_url) {
            form.action = result.remove_url;
        } else if (!result.saved && result.add_url) {
            form.action = result.add_url;
        }
        form.dataset.contentId = result.content_id;
        delete form.dataset.externalSave;

        const container = form.parentElement;
        if (container) {
            let favorite = container.querySelector('[data-favorite-form]');
            if (result.saved && result.favorite_url && !favorite) {
                const csrf = form.querySelector('input[name="csrfmiddlewaretoken"]');
                favorite = document.createElement('form');
                favorite.method = 'post';
                favorite.action = result.favorite_url;
                favorite.dataset.favoriteForm = '';
                favorite.dataset.favoriteState = result.favorite ? '1' : '0';
                favorite.innerHTML = `${csrf ? `<input type="hidden" name="csrfmiddlewaretoken" value="${csrf.value}">` : ''}<input type="hidden" name="favorite" value="${result.favorite ? '0' : '1'}"><button type="submit" class="btn btn-sm ${result.favorite ? 'btn-warning' : 'btn-outline-light'} w-100 mt-1">${result.favorite ? '★ Favorite' : '☆ Mark favorite'}</button>`;
                form.insertAdjacentElement('afterend', favorite);
            } else if (!result.saved && favorite) {
                favorite.remove();
            }
        }
    } catch (error) {
        console.error(error);
        button.textContent = originalLabel;
        window.alert('Could not update the watchlist. Please try again.');
    } finally {
        button.disabled = false;
    }
});
