document.addEventListener('submit', async (event) => {
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

        if (result.saved) {
            form.action = result.remove_url || `/watchlist/remove/${result.content_id}/`;
            form.dataset.contentId = result.content_id;
            delete form.dataset.externalSave;
        } else {
            form.action = `/watchlist/add/${result.content_id}/`;
        }
    } catch (error) {
        console.error(error);
        button.textContent = originalLabel;
        window.alert('Could not update the watchlist. Please try again.');
    } finally {
        button.disabled = false;
    }
});
